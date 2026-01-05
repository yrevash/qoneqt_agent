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
        candidate_profile: Dict[str, Any],
        user_query: str  
    ) -> list:
        
        # 1. Format the Candidate for the User Prompt
        candidate_str = (
            f"Candidate Name: {candidate_profile.get('full_name')}\n"
            f"Bio: {candidate_profile.get('bio')}\n"
            f"Location: {candidate_profile.get('location')}\n"
            f"Skills: {', '.join(candidate_profile.get('skills', []))}"
        )

        # 2. Dynamic System Prompt
        system_content = f"""You are an expert AI Connecting working for {user_profile.get('full_name')}.

YOUR CURRENT MISSION:
The user specifically asked: "{user_query}"

YOUR TASK:
Evaluate if the candidate below is a good match for this SPECIFIC request.
- If the user wants a "Rust Dev" and the candidate is a "React Dev", ACCEPT.
- If the user wants "Investors" and the candidate is a "Student", REJECT.

Output JSON:
{{
    "decision": "ACCEPT" | "REJECT",
    "confidence_score": 0.9,
    "reasoning": "Why they fit the query '{user_query}'...",
    "generated_message": "Draft a short connection request mentioning their specific relevant skills."
}}
"""

        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": f"Candidate Profile:\n{candidate_str}"}
        ]
        
        return messages
    

    SYSTEM_AUDITOR_V1 = """You are the Chief AI Auditor for the Qoneqt Network.
Your job is to review the actions of autonomous agents to ensure they are safe, polite, and logical.

INPUT CONTEXT:
- Agent Profile: {agent_context}
- Candidate Profile: {candidate_context}
- Agent's Decision: {decision}
- Agent's Reasoning: {reasoning}

TASK:
Evaluate the Agent's decision. 
1. **Hallucination Check**: Did the agent make up facts not in the profile?
2. **Safety Check**: Was the reasoning rude, biased, or aggressive?
3. **Logic Check**: Does the decision make sense given the profiles?

OUTPUT JSON:
{{
    "status": "PASS" | "FLAGGED",
    "risk_level": "LOW" | "MEDIUM" | "HIGH",
    "audit_reasoning": "Explanation of your verdict..."
}}
"""

    @staticmethod
    def build_auditor_prompt(trace_data: Dict[str, Any]) -> list:
        # Construct the supervision prompt
        return [
            {
                "role": "system", 
                "content": PromptTemplates.SYSTEM_AUDITOR_V1.format(
                    agent_context=trace_data.get('agent_bio', 'Unknown'),
                    candidate_context=trace_data.get('candidate_context', 'Unknown'),
                    decision=trace_data.get('decision'),
                    reasoning=trace_data.get('reasoning_log')
                )
            },
            {
                "role": "user", 
                "content": "Audit this interaction."
            }
        ]