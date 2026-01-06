"""
Fix missing vectors for existing users.
Run this once to populate interest_vector for users created before the fix.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.modules.identity.models import User
from app.modules.recsys.embedding import embedding_service

async def fix_vectors():
    async with AsyncSessionLocal() as session:
        # Find all users without vectors
        result = await session.execute(
            select(User).where(User.interest_vector.is_(None))
        )
        users_without_vectors = result.scalars().all()
        
        if not users_without_vectors:
            print("✅ All users already have vectors!")
            return
        
        print(f"Found {len(users_without_vectors)} users without vectors. Fixing...")
        
        for user in users_without_vectors:
            # Generate vector from bio + role + skills
            profile_text = f"{user.bio or ''} {user.role or ''} {' '.join(user.skills or [])}"
            
            if not profile_text.strip():
                profile_text = f"{user.full_name} user profile"
            
            vector = embedding_service.get_embedding(profile_text)
            user.interest_vector = vector
            
            print(f"✅ Fixed vector for: {user.full_name} ({user.email})")
        
        await session.commit()
        print(f"\n🎉 Successfully updated {len(users_without_vectors)} users!")

if __name__ == "__main__":
    asyncio.run(fix_vectors())
