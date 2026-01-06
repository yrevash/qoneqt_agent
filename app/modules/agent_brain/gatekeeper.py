import json
import logging
import httpx
from app.core.config import settings

logger = logging.getLogger("qoneqt.gatekeeper")

class GatekeeperService:
    """
    Layer 1.5: The Filter.
    Protects the system from junk, spam, and non-networking requests.
    """
    
    SYSTEM_PROMPT = """You are a Gatekeeper for a Networking AI Agent.
Your ONLY job is to classify if a user's input is a valid search request to find and connect with people.

VALID Criteria (ALLOW THESE):
- Looking for ANY type of person (professionals, athletes, artists, gamers, creators, etc.)
- Asking to find, connect with, or meet someone
- Searching by role, skill, interest, hobby, or any personal attribute
- Examples: "find investors", "connect with football players", "find AI engineers", "gamers who play Valorant"

INVALID Criteria (BLOCK THESE - VERY FEW):
- Pure greetings with no request ("Hi", "Hello")
- Complete gibberish ("asdf", "xkjdhf")
- Task requests unrelated to finding people ("Write code", "Summarize this article")
- Questions about the system itself ("How do you work?")

BE PERMISSIVE. This is a NETWORKING tool - people want to connect with ALL types of people, not just professionals.

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
            # Use Ollama's chat endpoint for classification
            payload = {
                "model": settings.OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": f"User Query: {query}"}
                ],
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": 0.0,
                    "num_predict": 50
                }
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{settings.OLLAMA_HOST}/api/chat",
                    json=payload
                )
                response.raise_for_status()
                
            result_json = response.json()
            raw_content = result_json.get('message', {}).get('content', '')
            
            # Simple parsing (strip markdown if present)
            clean_resp = raw_content.replace("```json", "").replace("```", "").strip()
            result = json.loads(clean_resp)
            
            if result.get("status") == "ALLOWED":
                return {"status": "ALLOWED"}
            
            return result

        except Exception as e:
            logger.error(f"Gatekeeper Error: {e}")
            # Fail-safe: Block on error to save credits
            return {"status": "BLOCKED", "reason": "Gatekeeper unavailable."}

gatekeeper_service = GatekeeperService()