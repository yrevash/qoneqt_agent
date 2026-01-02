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
        # We use a direct HTTP Client to avoid bloat from heavy SDKs
        # Assumption: vLLM is running at the URL defined in settings
        self.model_url = "http://vllm:8000/v1/chat/completions"
        self.model_name = "Qwen/Qwen2.5-7B-Instruct" 
        self.headers = {"Content-Type": "application/json"}
        # Timeout is crucial for production stability
        self.timeout = httpx.Timeout(30.0, connect=5.0)

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
            
            # 2. Call Inference Engine (vLLM)
            payload = {
                "model": self.model_name,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 500,
                # JSON Mode ensures the model tries to output valid JSON
                "response_format": {"type": "json_object"} 
            }

            logger.info(f"Brain Thinking... (Agent: {agent_profile['full_name']} -> Candidate: {candidate_profile['full_name']})")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.model_url, 
                    json=payload, 
                    headers=self.headers
                )
                response.raise_for_status()
                
            result_json = response.json()
            raw_content = result_json['choices'][0]['message']['content']

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