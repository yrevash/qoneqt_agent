import json
from typing import Dict, Any

class PromptTemplates:
    
    SYSTEM_SCREENER_V1 = """You are an autonomous AI Agent in the Qoneqt Professional Network.
Your goal is to evaluate a potential connection (Candidate) for your user (Me) based on our professional goals.

You must reply with ONLY a valid JSON object. Do not add markdown blocks or conversational filler.

Your Output Schema is:
{{
    "decision": "ACCEPT" | "REJECT" | "HOLD",
    "confidence_score": 0.95,
    "reasoning": "Short explanation...",
    "generated_message": "Hello [Name], I saw..." (Only if ACCEPT)
}}

My Profile:
{user_context}

Evaluation Criteria:
1. STRICTNESS LEVEL: {strictness}/10
2. **ACCEPT if the candidate:**
   - Works in the same industry or domain (e.g., both in blockchain, AI, finance, etc.)
   - Has complementary or related skills (even if different tech stacks)
   - Has a professional profile with relevant expertise
   - Match score >= 0.7

3. **REJECT if the candidate:**
   - Is completely unrelated to my professional domain
   - Appears to be a bot, spammer, or marketing account
   - Has inappropriate or unprofessional content
   - Match score < 0.5

4. **HOLD if uncertain** (requires human review)

5. If ACCEPT, write a personalized connection message (2-3 sentences) mentioning:
   - A specific skill or experience from their profile
   - Why you'd like to connect
   - Keep it professional and genuine
"""

    @staticmethod
    def build_screener_prompt(
        user_profile: Dict[str, Any],
        candidate_profile: Dict[str, Any]
    ) -> list:
        """
        Constructs the ChatML messages list for Qwen.
        """
        # 1. Format the User Context for the System Prompt
        user_context_str = (
            f"Name: {user_profile.get('full_name')}\n"
            f"Bio: {user_profile.get('bio')}\n"
            f"Location: {user_profile.get('location')}\n"
            f"Skills: {', '.join(user_profile.get('skills', []))}"
        )
        
        # 2. Format the Candidate for the User Prompt
        candidate_str = (
            f"Candidate Name: {candidate_profile.get('full_name')}\n"
            f"Bio: {candidate_profile.get('bio')}\n"
            f"Location: {candidate_profile.get('location')}\n"
            f"Match Score: {candidate_profile.get('match_score')}\n"
            f"Skills: {', '.join(candidate_profile.get('skills', []))}"
        )

        messages = [
            {
                "role": "system", 
                "content": PromptTemplates.SYSTEM_SCREENER_V1.format(
                    user_context=user_context_str,
                    strictness=7  # Default strictness
                )
            },
            {
                "role": "user", 
                "content": f"Evaluate this candidate:\n\n{candidate_str}"
            }
        ]
        
        return messages