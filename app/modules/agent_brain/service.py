import json
import logging
import httpx
from typing import Dict, Any, Optional
from app.core.config import settings
from app.modules.agent_brain.schemas import AgentDecision
from app.modules.agent_brain.prompts import PromptTemplates

logger = logging.getLogger("qoneqt.brain")

class InferenceService:
    """
    Layer 4: The Brain.
    Manages LLM interaction, prompt construction, and safety validation.
    """
    
    def __init__(self):
        # Using Ollama on host
        self.model_url = f"{settings.OLLAMA_HOST}/api/chat"
        self.model_name = settings.OLLAMA_MODEL
        # Longer timeout for vision/larger models
        self.timeout = httpx.Timeout(300.0, connect=10.0)

    async def decide_on_candidate(
        self, 
        agent_profile: Dict[str, Any], 
        candidate_profile: Dict[str, Any]
    ) -> Optional[AgentDecision]:
        """
        Main Entry Point: Evaluates a candidate and returns a structured decision.
        """
        try:
            # 1. Build Prompt
            messages = PromptTemplates.build_screener_prompt(agent_profile, candidate_profile)
            
            # 2. Call Inference Engine (Ollama)
            payload = {
                "model": self.model_name,
                "messages": messages,
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": 0.7,
                    "num_predict": 500,
                }
            }

            logger.info(f"Brain Thinking... (Agent: {agent_profile['full_name']} -> Candidate: {candidate_profile['full_name']})")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.model_url, 
                    json=payload
                )
                response.raise_for_status()
                
            result_json = response.json()
            raw_content = result_json['message']['content']
            
            # Debug: print raw response
            print(f"DEBUG Raw Response: {raw_content[:500]}...")

            # 3. Parse & Validate (The Safety Guardrail)
            decision_data = self._clean_and_parse_json(raw_content)
            validated_decision = AgentDecision(**decision_data)
            
            logger.info(f"Thought Complete: {validated_decision.decision} (Reason: {validated_decision.reasoning[:50]}...)")
            return validated_decision

        except Exception as e:
            logger.error(f"Brain Failure: {str(e)}")
            # Fail safe: Return None or a default REJECT object
            return None

    def _clean_and_parse_json(self, raw_text: str) -> Dict:
        """
        Helper to robustly extract JSON from LLM chatter.
        """
        try:
            # Attempt direct parse
            return json.loads(raw_text)
        except json.JSONDecodeError:
            # Heuristic: Find the first { and last }
            start = raw_text.find("{")
            end = raw_text.rfind("}") + 1
            if start != -1 and end != -1:
                return json.loads(raw_text[start:end])
            raise ValueError("Could not extract JSON from model output")

# Singleton Export
inference_service = InferenceService()