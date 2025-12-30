import asyncio
import sys
import os
from sqlalchemy import select

# Add project root to path
sys.path.append(os.getcwd())

from app.core.database import AsyncSessionLocal
from app.modules.identity.models import User
from app.modules.recsys.embedding import embedding_service

async def search_for_agent(query_text: str):
    print(f"\n🔍 Searching for: '{query_text}'")
    
    # 1. Convert Query to Vector
    # This runs the local AI model on the search string
    # Run in executor to avoid event loop conflicts
    loop = asyncio.get_event_loop()
    query_vector = await loop.run_in_executor(
        None, embedding_service.get_embedding, query_text
    )
    
    async with AsyncSessionLocal() as session:
        # 2. The Magic Query (Postgres + pgvector)
        # We use the <=> operator (Cosine Distance) via the ORM
        # Ordering by distance ASC gives the most similar results.
        stmt = select(User).order_by(
            User.interest_vector.cosine_distance(query_vector)
        ).limit(3)
        
        result = await session.execute(stmt)
        users = result.scalars().all()
        
        print(f"   Top 3 Matches:")
        for i, user in enumerate(users):
            # Print Name and a snippet of Bio to verify relevance
            print(f"   {i+1}. {user.full_name} ({user.bio[:60]}...)")

async def main():
    # Test 1: Finding a Security Expert (Should find 'Bob Solidity')
    await search_for_agent("I need a security expert to audit my smart contracts")
    
    # Test 2: Finding an Investor (Should find 'Frank Founder' or 'Ivy Investor')
    await search_for_agent("Looking for funding for my ZK startup")
    
    # Test 3: Finding Infrastructure (Should find 'Dave DevOps')
    await search_for_agent("Who knows about running validators and nodes?")

if __name__ == "__main__":
    asyncio.run(main())