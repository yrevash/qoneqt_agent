import math
from datetime import datetime

class RankingEngine:
    """
    Production Scoring Engine.
    Formula: Score = (Semantic_Sim * 0.5) + (Social_Proof * 0.3) + (Recency * 0.2)
    
    Weights are adjustable based on business logic.
    """

    @staticmethod
    def calculate_score(
        cosine_distance: float, 
        last_active_at: datetime, 
        fan_count: int
    ) -> float:
        # 1. Semantic Similarity (Converted from Distance)
        # PGVector Cosine Distance is (1 - Cosine Similarity).
        # Range: 0.0 (Identical) to 2.0 (Opposite).
        # We clamp it to ensure we get a 0.0-1.0 similarity score.
        raw_similarity = 1.0 - cosine_distance
        similarity_score = max(0.0, min(1.0, raw_similarity))

        # 2. Recency Decay (Sigmoid Decay)
        # Users active within 7 days get ~1.0. Users inactive for 90 days get ~0.1.
        if last_active_at:
            days_inactive = (datetime.utcnow() - last_active_at).days
            # Logic: 1 / (1 + days/30) -> Slow decay
            recency_score = 1.0 / (1.0 + (max(0, days_inactive) / 30.0))
        else:
            recency_score = 0.5 # Neutral penalty for unknown activity

        # 3. Social Proof (Logarithmic Normalization)
        # We use Log10 so 10k followers isn't 1000x better than 10 followers.
        # Scale: 0 followers = 0.0, 1000 followers = ~3.0.
        # We normalize this to a 0-1 scale assuming a "Whale" has ~10k followers (cap at 4.0).
        log_fans = math.log10(fan_count + 1)
        social_score = min(1.0, log_fans / 4.0)

        # 4. Weighted Aggregate (The Business Logic)
        # Phase 3 Priority: Semantic Match is King (50%), Social is Queen (30%), Freshness is Jack (20%).
        final_score = (
            (similarity_score * 0.50) + 
            (social_score * 0.30) + 
            (recency_score * 0.20)
        )

        return round(final_score, 4)