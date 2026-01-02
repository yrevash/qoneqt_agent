import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from app.modules.agent_brain.service import inference_service

# Mock Data (What the RecSys would normally provide)
MOCK_AGENT = {
    "full_name": "Alice Rust",
    "bio": "Senior Rust Engineer building ZK-Rollups on Solana.",
    "location": "San Francisco, USA",
    "skills": ["Rust", "Solana", "ZK", "Cryptography"]
}

MOCK_CANDIDATE_GOOD = {
    "full_name": "Bob Solidity",
    "bio": "Smart Contract Auditor. Expert in Reentrancy attacks.",
    "location": "London, UK",
    "match_score": 0.85,
    "skills": ["Solidity", "Security", "EVM"]
}

MOCK_CANDIDATE_BAD = {
    "full_name": "Spam Bot 3000",
    "bio": "I sell cheap followers and crypto marketing services. DM me!",
    "location": "Unknown",
    "match_score": 0.10,
    "skills": ["Marketing", "Sales"]
}

async def test_brain():
    print("🧠 Initializing Brain Connection (Qwen 7B via vLLM)...")
    
    # TEST 1: Good Match
    print(f"\n🧪 TEST 1: Evaluating {MOCK_CANDIDATE_GOOD['full_name']} (Should ACCEPT)")
    decision = await inference_service.decide_on_candidate(MOCK_AGENT, MOCK_CANDIDATE_GOOD)
    
    if decision:
        print(f"   ✅ Decision: {decision.decision}")
        print(f"   📊 Confidence: {decision.confidence_score}")
        print(f"   🤔 Reasoning: {decision.reasoning}")
        print(f"   💬 Message: {decision.generated_message}")
    else:
        print("   ❌ Brain Failed (Connection Error or Timeout)")

    # TEST 2: Bad Match
    print(f"\n🧪 TEST 2: Evaluating {MOCK_CANDIDATE_BAD['full_name']} (Should REJECT)")
    decision_bad = await inference_service.decide_on_candidate(MOCK_AGENT, MOCK_CANDIDATE_BAD)
    
    if decision_bad:
        print(f" Decision: {decision_bad.decision}")
        print(f" Reasoning: {decision_bad.reasoning}")
    else:
        print(" Brain Failed")

if __name__ == "__main__":
    asyncio.run(test_brain())