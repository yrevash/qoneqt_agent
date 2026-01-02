import json
import logging
import httpx
import re
from typing import Dict, Any, Optional
from app.core.config import settings
from app.modules.agent_brain.schemas import AgentDecision
from app.modules.agent_brain.prompts import PromptTemplates

logger = logging.getLogger("qoneqt.brain")

class InferenceService:
    """
    Layer 4: The Brain (Ollama Implementation).
    """
    
    def __init__(self):
        # Ensure we hit the chat endpoint
        self.model_url = f"{settings.OLLAMA_HOST}/api/chat"
        self.model_name = settings.OLLAMA_MODEL
        # 30s is usually enough for local GPU inference
        self.timeout = httpx.Timeout(30.0, connect=5.0)

    async def decide_on_candidate(
        self, 
        agent_profile: Dict[str, Any], 
        candidate_profile: Dict[str, Any]
    ) -> Optional[AgentDecision]:
        try:
            # 1. Build Prompt
            messages = PromptTemplates.build_screener_prompt(agent_profile, candidate_profile)
            
            # 2. Call Ollama
            payload = {
                "model": self.model_name,
                "messages": messages,
                "stream": False,
                "format": "json",  # Forces JSON mode
                "options": {
                    "temperature": 0.2, # Lower temp = more consistent JSON
                    "num_ctx": 4096,    # Context window
                    "num_gpu": -1       # Force all layers to GPU
                }
            }

            logger.info(f"Brain Thinking... (Model: {self.model_name})")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.model_url, json=payload)
                response.raise_for_status()
                
            result_json = response.json()
            raw_content = result_json.get('message', {}).get('content', '')

            # DEBUG: Print what the model actually said
            print(f"\nRAW MODEL OUTPUT:\n{raw_content}\n")

            # 3. Robust Parsing
            decision_data = self._clean_and_parse_json(raw_content)
            
            # 4. Validate with Pydantic
            validated_decision = AgentDecision(**decision_data)
            
            logger.info(f"✅ Decision: {validated_decision.decision}")
            return validated_decision

        except Exception as e:
            logger.error(f"❌ Brain Failure: {e}")
            return None

    def _clean_and_parse_json(self, raw_text: str) -> Dict:
        """
        Robustly extracts JSON, handling markdown blocks and messy output.
        """
        try:
            # 1. Try direct parse first
            return json.loads(raw_text)
        except json.JSONDecodeError:
            pass

        # 2. Strip Markdown Code Blocks (```json ... ```)
        # Regex to find content between ```json (or just ```) and ```
        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw_text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # 3. Last Resort: Find the first '{' and the last '}'
        start = raw_text.find("{")
        end = raw_text.rfind("}") + 1
        
        if start != -1 and end != -1:
            clean_text = raw_text[start:end]
            try:
                return json.loads(clean_text)
            except json.JSONDecodeError:
                # Sometimes models add trailing commas which breaks standard JSON
                # Simple fix for trailing commas before closing braces
                clean_text = re.sub(r",\s*}", "}", clean_text)
                return json.loads(clean_text)
                
        raise ValueError(f"Could not extract JSON. Raw content: {raw_text[:50]}...")

# Singleton Export
inference_service = InferenceService()