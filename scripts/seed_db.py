import asyncio
import sys
import os
import uuid

# Add project root to path so Python can find 'app'
sys.path.append(os.getcwd())

from app.core.database import AsyncSessionLocal
from app.modules.identity.models import User
from app.modules.recsys.embedding import embedding_service

# High-Quality Mock Data
# We mix different personas to test if the search can distinguish them.
MOCK_USERS = [
    # ---------------- BLOCKCHAIN DEVS ----------------
    {
        "name": "Alice Rust", 
        "bio": "Senior Rust Engineer building ZK-Rollups on Solana. 5 years experience with low-level systems programming."
    },
    {
        "name": "Bob Solidity", 
        "bio": "Smart Contract Auditor. Expert in Reentrancy attacks and EVM security. Previously at OpenZeppelin."
    },
    {
        "name": "Charlie Chain", 
        "bio": "Full stack Web3 developer. React + Hardhat. Building a Decentralized Exchange (DEX) on Polygon."
    },
    {
        "name": "Dave DevOps",
        "bio": "Infrastructure engineer for blockchain nodes. Kubernetes expert. Running validators for Eth2."
    },
    {
        "name": "Eve Encryption",
        "bio": "Cryptography researcher. Zero Knowledge Proofs and MPC wallets. Mathematics PhD."
    },

    # ---------------- INVESTORS (VCs) ----------------
    {
        "name": "Frank Founder", 
        "bio": "Angel Investor looking for pre-seed ZK-Rollup projects. Focused on privacy and scaling solutions."
    },
    {
        "name": "Grace Growth", 
        "bio": "Head of Growth at a major DeFi protocol. Looking for partnerships with wallet providers."
    },
    {
        "name": "Hank Hedge",
        "bio": "Quant trader moving into venture capital. Interested in Arbitrum ecosystem and high-frequency trading infrastructure."
    },
    {
        "name": "Ivy Investor",
        "bio": "Partner at CryptoVentures. Focused on Infrastructure and Privacy middleware."
    },

    # ---------------- OUTLIERS (Noise) ----------------
    {
        "name": "Harry Hiker", 
        "bio": "Professional wilderness guide. I love hiking and nature photography. Not technical."
    }
]

async def seed():
    print("🌱 Starting Database Seed...")
    
    # Ensure the embedding service is ready (this might trigger model download)
    # We call a dummy embedding to force load if it's lazy loaded
    _ = embedding_service.get_embedding("warmup")
    
    async with AsyncSessionLocal() as session:
        count = 0
        for persona in MOCK_USERS:
            print(f"   Processing: {persona['name']}...")
            
            # 1. THE PROCESSING LAYER: Text -> Vector
            # This uses the local 'all-mpnet-base-v2' model (768 dims)
            vector = embedding_service.get_embedding(persona['bio'])
            
            # 2. THE STORAGE LAYER: Save to Postgres
            # We generate a consistent email for testing
            email = f"{persona['name'].split()[0].lower()}@qoneqt.com"
            
            # Check if user already exists to avoid unique constraint errors on re-runs
            # (Optional check, but good for dev scripts)
            # existing = await session.execute(select(User).where(User.email == email))
            # if existing.scalars().first(): continue 

            user = User(
                id=uuid.uuid4(),
                email=email,
                full_name=persona['name'],
                bio=persona['bio'],
                interest_vector=vector,
                is_active=True,
                # Default Schedule: Active 9am-5pm (Hours 9-17)
                # 0-8: 0.0, 9-17: 0.8, 18-23: 0.0
                activity_schedule=[0.0]*9 + [0.8]*9 + [0.0]*6
            )
            session.add(user)
            count += 1
        
        await session.commit()
        print(f"✅ Database Seeded Successfully! ({count} Users Created)")

if __name__ == "__main__":
    asyncio.run(seed())