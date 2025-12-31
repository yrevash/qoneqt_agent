import asyncio
import sys
import os
import uuid
from sqlalchemy import select

sys.path.append(os.getcwd())

from app.core.database import AsyncSessionLocal
from app.modules.identity.models import User
from app.modules.recsys.embedding import embedding_service

MOCK_USERS = [
    {
        "name": "Alice Rust", 
        "bio": "Senior Rust Engineer building ZK-Rollups on Solana. 5 years experience with low-level systems programming.",
        "location": "San Francisco, USA",
        "role": "Engineer",
        "skills": ["Rust", "Solana", "ZK"]
    },
    {
        "name": "Bob Solidity", 
        "bio": "Smart Contract Auditor. Expert in Reentrancy attacks and EVM security. Previously at OpenZeppelin.",
        "location": "London, UK",
        "role": "Auditor",
        "skills": ["Solidity", "Security", "EVM"]
    },
    {
        "name": "Charlie Chain", 
        "bio": "Full stack Web3 developer. React + Hardhat. Building a Decentralized Exchange (DEX) on Polygon.",
        "location": "Bangalore, India",
        "role": "Engineer",
        "skills": ["React", "Hardhat", "Polygon"]
    },
    {
        "name": "Dave DevOps",
        "bio": "Infrastructure engineer for blockchain nodes. Kubernetes expert. Running validators for Eth2.",
        "location": "Berlin, Germany",
        "role": "DevOps",
        "skills": ["Kubernetes", "AWS", "Linux"]
    },
    {
        "name": "Eve Encryption",
        "bio": "Cryptography researcher. Zero Knowledge Proofs and MPC wallets. Mathematics PhD.",
        "location": "Zurich, Switzerland",
        "role": "Researcher",
        "skills": ["Cryptography", "Math", "MPC"]
    },
    # ---------------- INDIAN DEV SCENARIO ----------------
    {
        "name": "Rohan React", 
        "bio": "Frontend wizard specializing in Web3 integrations. Love building clean UI for DeFi protocols.",
        "location": "Bangalore, India",
        "role": "Engineer",
        "skills": ["React", "Typescript", "Web3.js"]
    },

    # ---------------- INVESTORS (VCs) ----------------
    {
        "name": "Frank Founder", 
        "bio": "Angel Investor looking for pre-seed ZK-Rollup projects. Focused on privacy and scaling solutions.",
        "location": "New York, USA",
        "role": "Investor",
        "skills": ["Investing", "Strategy"]
    },
    {
        "name": "Grace Growth", 
        "bio": "Head of Growth at a major DeFi protocol. Looking for partnerships with wallet providers.",
        "location": "Singapore",
        "role": "Growth",
        "skills": ["Marketing", "Partnerships"]
    },
]

async def seed():
    print("🌱 Starting Database Seed (V2 with Metadata)...")
    
    _ = embedding_service.get_embedding("warmup")
    
    async with AsyncSessionLocal() as session:
        count = 0
        for persona in MOCK_USERS:
            print(f"   Processing: {persona['name']} ({persona['location']})...")
            
            vector = embedding_service.get_embedding(persona['bio'])
            email = f"{persona['name'].split()[0].lower()}@qoneqt.com"
            
            # Upsert logic (simplified: check existence by email)
            existing = await session.execute(select(User).where(User.email == email))
            if existing.scalars().first():
                print(f"   ⚠️  Skipping {persona['name']} (Already exists)")
                continue

            user = User(
                id=uuid.uuid4(),
                email=email,
                full_name=persona['name'],
                bio=persona['bio'],
                
                # NEW FIELDS
                location=persona['location'],
                role=persona['role'],
                skills=persona['skills'],
                
                interest_vector=vector,
                is_active=True,
                activity_schedule=[0.0]*9 + [0.8]*9 + [0.0]*6
            )
            session.add(user)
            count += 1
        
        await session.commit()
        print(f"✅ Database Seeded Successfully! ({count} New Users Created)")

if __name__ == "__main__":
    asyncio.run(seed())