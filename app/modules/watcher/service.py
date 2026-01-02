import json
import logging
from sqlalchemy import select, desc
from app.core.database import AsyncSessionLocal
from app.modules.identity.models import AgentTrace, User
from app.modules.agent_brain.inference import llm_client
from app.modules.agent_brain.prompts import PromptTemplates

logger = logging.getLogger("qoneqt.auditor")

class AuditorService:
    async def run_audit_cycle(self):
        logger.info(" Starting AI Audit Cycle...")
        
        async with AsyncSessionLocal() as session:
            # 1. Fetch recent traces (e.g., last 10 for demo)
            # In production, you would flag 'audited=False' columns
            stmt = select(AgentTrace).order_by(desc(AgentTrace.created_at)).limit(10)
            result = await session.execute(stmt)
            traces = result.scalars().all()
            
            for trace in traces:
                # 2. Reconstruct Context ( Simplified for demo )
                # Ideally, we should store snapshots of profiles, but we'll fetch current state
                agent = await session.get(User, trace.agent_id)
                
                audit_payload = {
                    "agent_bio": agent.bio if agent else "Unknown",
                    "candidate_context": "Stored in trace logs in v2", # Placeholder
                    "decision": trace.decision,
                    "reasoning_log": trace.reasoning_log
                }
                
                # 3. Ask the Brain to Audit
                messages = PromptTemplates.build_auditor_prompt(audit_payload)
                response = await llm_client.chat(messages, temperature=0.0)
                
                # 4. Parse & Log
                try:
                    audit_result = json.loads(response)
                    if audit_result.get("status") == "FLAGGED":
                        logger.warning(f"FLAGGED INTERACTION ({trace.id}): {audit_result['audit_reasoning']}")
                    else:
                        logger.info(f"PASSED ({trace.id}): Logic seems sound.")
                except Exception:
                    logger.error(f"Failed to parse audit for {trace.id}")

auditor_service = AuditorService()