import json
import logging
from app.modules.agent_brain.inference import llm_client

logger = logging.getLogger("qoneqt.gatekeeper")

class GatekeeperService:
    """
    Layer 1.5: The Filter.
    Protects the system from junk, spam, and non-networking requests.
    """
    
    SYSTEM_PROMPT = """You are a Gatekeeper for a Professional Networking AI.
Your ONLY job is to classify if a user's input is a valid networking search request.

VALID Criteria:
- Asking to find, connect, or hire someone.
- Asking for introductions to specific roles (Devs, Investors, etc).
- Looking for people in specific industries.

INVALID Criteria (JUNK):
- Greetings ("Hi", "Hello").
- Gibberish ("asdf", "test").
- Task requests ("Write code", "Summarize this").
- General knowledge questions ("What is Bitcoin?").

OUTPUT FORMAT:
Reply with ONLY a JSON object: {"status": "ALLOWED"} or {"status": "BLOCKED", "reason": "Short reason..."}
"""

    async def validate_request(self, query: str) -> dict:
        """
        Returns {'status': 'ALLOWED'} or {'status': 'BLOCKED', 'reason': '...'}
        """
        if not query or len(query.strip()) < 5:
            return {"status": "BLOCKED", "reason": "Query too short."}

        try:
            # We use a very low temperature for strict classification
            response = await llm_client.generate(
                prompt=f"User Query: {query}",
                system=self.SYSTEM_PROMPT,
                temperature=0.0,
                max_tokens=50
            )
            
            # Simple parsing (assuming the model follows the strict JSON instruction)
            # In a prod environment, we'd use the robust parser, but this needs to be fast.
            # We strip markdown just in case.
            clean_resp = response.replace("```json", "").replace("```", "").strip()
            result = json.loads(clean_resp)
            
            if result.get("status") == "ALLOWED":
                return {"status": "ALLOWED"}
            
            return result

        except Exception as e:
            logger.error(f"Gatekeeper Error: {e}")
            # Fail-safe: If Gatekeeper crashes, do we block or allow? 
            # Safe mode = Block to save credits. Permissive = Allow.
            return {"status": "BLOCKED", "reason": "Gatekeeper unavailable."}

gatekeeper_service = GatekeeperService()