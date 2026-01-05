import asyncio
import uuid
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import AsyncSessionLocal
from app.modules.identity.models import User
from app.modules.recsys.embedding import embedding_service

async def add_myself():
    email = "yashtiwari9182@gmail.com"
    full_name = "Yash Tiwari"
    
    print(f"Creating user: {email}...")
    
    # Generate a dummy vector for now
    vector = embedding_service.get_embedding("I am the creator of this network.")
    
    async with AsyncSessionLocal() as session:
        user = User(
            id=uuid.uuid4(),
            email=email,
            full_name=full_name,
            bio="System Administrator",
            location="India",
            role="Admin",
            skills=["Python", "Architecture", "FastAPI"],
            interest_vector=vector,
            is_active=True,
            activity_schedule=[1.0] * 24 # Always awake
        )
        session.add(user)
        await session.commit()
        print(f"✅ User {email} added successfully!")

if __name__ == "__main__":
    asyncio.run(add_myself())