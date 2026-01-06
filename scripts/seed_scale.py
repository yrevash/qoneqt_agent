import asyncio
import sys
import os
import uuid
import random
import time
from faker import Faker
from tqdm import tqdm
from sqlalchemy import select

# Setup Path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import AsyncSessionLocal
from app.modules.identity.models import User

fake = Faker()

# Roles to make the "Brain" logic work occasionally
ROLES = ["Rust Developer", "Solidity Engineer", "Marketing Lead", "DevOps Engineer", "Product Manager", "Investor", "Data Scientist"]
SKILLS = {
    "Rust Developer": ["Rust", "Actix", "Tokio", "Systems"],
    "Solidity Engineer": ["Solidity", "EVM", "Hardhat", "Foundry"],
    "DevOps Engineer": ["Kubernetes", "AWS", "Terraform", "CI/CD"],
    "Investor": ["Venture Capital", "Finance", "DeFi", "Strategy"]
}

async def seed_scale(count=1000):
    print(f" Starting Mass Seed: {count} Users...")
    
    users_batch = []
    for _ in tqdm(range(count)):
        # 1. Create Realistic Profile
        role = random.choice(ROLES)
        role_skills = SKILLS.get(role, ["General"])
        name = fake.name()
        
        # 2. Fake Vector (Random) for Speed
        # Real vectors would take too long for 5k users on CPU
        # Since we are testing LOAD (Database/Worker), random vectors are fine.
        fake_vector = [random.random() for _ in range(768)]
        
        user = User(
            id=uuid.uuid4(),
            email=f"{name.replace(' ', '.').lower()}_{random.randint(1000,9999)}@test.com",
            full_name=name,
            bio=f"I am a {role} based in {fake.city()}. Passionate about {role_skills[0]}.",
            location=fake.country(),
            role=role,
            skills=role_skills,
            interest_vector=fake_vector,
            is_active=True,
            # Randomize sleep schedules (some awake at 9, some at 10, etc)
            activity_schedule=[random.choice([0.0, 1.0]) for _ in range(24)]
        )
        users_batch.append(user)

    print(" Saving to Database...")
    async with AsyncSessionLocal() as session:
        session.add_all(users_batch)
        await session.commit()
    
    print(f" Successfully added {count} users!")

if __name__ == "__main__":
    # Change number here (e.g., 5000)
    asyncio.run(seed_scale(1000))