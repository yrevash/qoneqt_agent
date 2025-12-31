import uuid
import logging
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy import select, text, and_, or_
from app.core.database import AsyncSessionLocal
from app.core.redis import RedisClient
from app.modules.identity.models import User
from app.modules.recsys.embedding import embedding_service
from app.modules.recsys.ranking import RankingEngine

# Configure structured logging
logger = logging.getLogger(__name__)

class RecSysService:
    
    async def get_recommendations(
        self, 
        initiator_id: uuid.UUID, 
        query_text: str, 
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 20,
        enable_smart_location: bool = True
    ) -> List[Dict]:
        """
        Production Implementation of the Matchmaking Funnel.
        
        Flow:
        1. Context Resolution: Determine rigid filters vs soft defaults.
        2. Vector Embedding: Convert query to 768-dim vector.
        3. Database Retrieval: Fetch (User, Distance) tuples using pgvector operator.
        4. Fast Data Enrichment: Pipeline fetch follower counts from Redis.
        5. Ranking: Apply mathematical scoring model.
        """
        filters = filters or {}
        
        async with AsyncSessionLocal() as session:
            # --- 1. CONTEXT RESOLUTION (The Cascade) ---
            initiator = await session.get(User, initiator_id)
            if not initiator:
                logger.error(f"Initiator {initiator_id} not found.")
                return []

            # Resolve Location Filter
            final_location_filter = None
            
            # Case A: Explicit Filter (User clicked a dropdown)
            if filters.get("location"):
                final_location_filter = filters.get("location")
                logger.info(f"[Explicit] Filtering by location: {final_location_filter}")
            
            # Case B: Smart Default (User said nothing, but we check their profile)
            elif enable_smart_location and initiator.location:
                final_location_filter = initiator.location
                logger.info(f"[Implicit] Defaulting to user location: {final_location_filter}")
            
            # Case C: Global Fallback (User has no location, filter is None) -> Global Search
            else:
                logger.info("[Global] No location context available. Searching globally.")

            # --- 2. VECTOR EMBEDDING ---
            query_vector = embedding_service.get_embedding(query_text)


            # --- 3. DATABASE RETRIEVAL (The Truth Source) ---
            # KEY CHANGE: We select the User AND the calculated Distance
            distance_col = User.interest_vector.cosine_distance(query_vector).label("distance")
            
            stmt = select(User, distance_col).where(
                User.id != initiator_id,
                User.is_active == True
            )

            # Apply Location Filter (if resolved)
            if final_location_filter:
                stmt = stmt.where(User.location.ilike(f"%{final_location_filter}%"))
            
            # Apply Other Explicit Filters (Role, Skills)
            if filters.get("role"):
                stmt = stmt.where(User.role.ilike(f"%{filters.get('role')}%"))
                
            # Order by Vector Distance (Nearest Neighbors) and limit retrieval pool
            # We fetch 3x the limit to allow the Ranking Engine to re-sort based on other factors
            retrieval_limit = limit * 3
            stmt = stmt.order_by(distance_col).limit(retrieval_limit)

            result = await session.execute(stmt)
            # Returns list of tuples: [(UserObject, 0.15), (UserObject, 0.22)...]
            hits = result.all() 

            if not hits:
                return []


            # --- 4. FAST DATA ENRICHMENT (Redis) ---
            candidate_ids = [str(row[0].id) for row in hits]
            fan_counts = await RedisClient.get_follower_counts(candidate_ids)


            # --- 5. SCORING & RANKING (The Logic) ---
            scored_candidates = []
            
            for i, (candidate, distance) in enumerate(hits):
                # We use the REAL distance from the DB, not the loop index.
                
                final_score = RankingEngine.calculate_score(
                    cosine_distance=distance,  # The mathematical truth
                    last_active_at=candidate.updated_at,
                    fan_count=fan_counts[i]
                )
                
                scored_candidates.append({
                    "user_id": str(candidate.id),
                    "full_name": candidate.full_name,
                    "bio": candidate.bio,
                    "location": candidate.location,
                    "role": candidate.role,
                    "match_score": final_score,
                    # Debug info is crucial for refining the algorithm later
                    "_debug": {
                        "vector_dist": round(distance, 4),
                        "fans": fan_counts[i],
                        "recency": str(candidate.updated_at)
                    }
                })

            # Re-sort based on our composite score (High to Low)
            scored_candidates.sort(key=lambda x: x["match_score"], reverse=True)
            
            return scored_candidates[:limit]

# Singleton instance
recsys_service = RecSysService()