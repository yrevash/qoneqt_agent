#!/usr/bin/env python3
"""
Quick script to generate a JWT token for development.
This will create a token for the first user in the database.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.core.security import create_access_token
from app.modules.identity.models import User

async def main():
    print("🔐 Generating JWT Token for Development...\n")
    
    async with AsyncSessionLocal() as session:
        # Get first user (or you can specify email)
        result = await session.execute(select(User).limit(1))
        user = result.scalars().first()
        
        if not user:
            print("❌ No users found in database.")
            print("💡 Run 'python scripts/seed_db.py' first to create test users.")
            return
        
        # Generate token
        token = create_access_token(data={"sub": str(user.id)})
        
        print(f"✅ Token generated for user:")
        print(f"   Name: {user.full_name}")
        print(f"   Email: {user.email}")
        print(f"   User ID: {user.id}")
        print(f"\n📋 Your JWT Token:\n")
        print(f"{token}\n")
        print(f"🔧 Copy this token and paste it into:")
        print(f"   qoneqt_web/src/lib/api.ts")
        print(f"   Replace 'YOUR_LONG_JWT_TOKEN_HERE' with the token above.\n")

if __name__ == "__main__":
    asyncio.run(main())
