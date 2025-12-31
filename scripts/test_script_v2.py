import asyncio
import sys
import os
import uuid
from sqlalchemy import select

sys.path.append(os.getcwd())

from app.core.database import AsyncSessionLocal
from app.modules.identity.models import User
from app.modules.recsys.service import recsys_service

async def get_or_create_test_agent(session, name, location=None):
    """Helper to get a user for testing context."""
    stmt = select(User).where(User.full_name == name)
    result = await session.execute(stmt)
    user = result.scalars().first()
    
    if not user:
        user = User(
            id=uuid.uuid4(),
            email=f"temp_{name.lower().replace(' ', '_')}@test.com",
            full_name=name,
            location=location,
            bio="Temporary test user",
            is_active=True
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
    
    return user

async def print_results(title, results):
    print(f"\n--- {title} ---")
    if not results:
        print("   ❌ No candidates found.")
        return

    for i, item in enumerate(results):
        user_name = item['full_name']
        loc = item['location'] or "Unknown"
        score = item['match_score']
        debug = item['_debug']
        
        print(f"   {i+1}. {user_name:<20} | 📍 {loc:<15} | 🏆 {score} | "
              f"Dist: {debug['vector_dist']:.3f}, Fans: {debug['fans']}")

async def main():
    print("Starting RecSys V2 Intelligence Test...\n")
    
    async with AsyncSessionLocal() as session:
        # ---------------------------------------------------------
        # SCENARIO 1: The "Local" User (Rohan from Bangalore)
        # ---------------------------------------------------------
        # Rohan is in Bangalore. He searches for "Developer".
        # EXPECTATION: The system should implicitly filter for 'Bangalore' or 'India'.
        rohan = await get_or_create_test_agent(session, "Rohan React")
        
        if rohan:
            print(f"👤 Testing as: {rohan.full_name} (Location: {rohan.location})")
            
            # Test A: Implicit Search (No filters)
            results_implicit = await recsys_service.get_recommendations(
                initiator_id=rohan.id,
                query_text="looking for a smart contract developer",
                limit=5
            )
            await print_results("TEST 1: Implicit Context (Should show India/Bangalore)", results_implicit)

            # Test B: Explicit Override
            # Rohan specifically wants someone in the USA, ignoring his own location.
            results_explicit = await recsys_service.get_recommendations(
                initiator_id=rohan.id,
                query_text="looking for a smart contract developer",
                filters={"location": "USA"}, # <--- OVERRIDE
                limit=5
            )
            await print_results("TEST 2: Explicit Override (Should show USA)", results_explicit)
        else:
            print("⚠️ Skipping Scenario 1: 'Rohan React' not found. Did you run seed_db.py?")

        # ---------------------------------------------------------
        # SCENARIO 2: The "Digital Nomad" (User with NO Location)
        # ---------------------------------------------------------
        # We create a user with location=None.
        # EXPECTATION: System should fall back to Global Search (Result mix of USA, India, UK).
        nomad = await get_or_create_test_agent(session, "Nomad Neil", location=None)
        
        print(f"\n👤 Testing as: {nomad.full_name} (Location: {nomad.location})")
        
        results_global = await recsys_service.get_recommendations(
            initiator_id=nomad.id,
            query_text="looking for a smart contract developer",
            limit=5
        )
        await print_results("TEST 3: Global Fallback (Should show mixed locations)", results_global)

if __name__ == "__main__":
    asyncio.run(main())