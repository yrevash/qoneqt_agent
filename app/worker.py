import sys
from pathlib import Path

# Ensure project root is on `sys.path` so running this file directly works
# e.g. `python ./app/worker.py` from the repository root
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import asyncio
import json
import logging
import aio_pika
from uuid import UUID

from app.core.config import settings
from app.core.queue import RabbitMQClient
from app.core.database import AsyncSessionLocal
from app.modules.identity.models import User, AgentTrace
from app.modules.recsys.service import recsys_service

# IMPORT THE NEW BRAIN
from app.modules.agent_brain.service import inference_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("qoneqt.worker")

class AgentWorker:
    async def start(self):
        # ... (Same connection logic as before) ...
        connection = await RabbitMQClient.get_connection()
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)
        
        queue = await channel.declare_queue("queue.high_priority", durable=True)
        await queue.consume(self.process_message)
        logger.info(" Agent Worker (Inference Enabled) Listening...")
        await asyncio.Future()

    async def process_message(self, message: aio_pika.IncomingMessage):
        async with message.process():
            try:
                payload = json.loads(message.body)
                agent_id_str = payload.get("agent_id")
                
                async with AsyncSessionLocal() as session:
                    # 1. Hydrate Context
                    agent = await session.get(User, UUID(agent_id_str))
                    if not agent: return

                    # 2. Get Candidates (Layer 3)
                    recommendations = await recsys_service.get_recommendations(
                        initiator_id=agent.id,
                        query_text="Find relevant peers",
                        limit=1
                    )
                    
                    if not recommendations:
                        logger.info("No candidates found.")
                        return

                    candidate = recommendations[0]

                    # 3. RUN INFERENCE (Layer 4)
                    # Convert SQLAlchemy model to Dict for the Brain
                    agent_profile = {
                        "full_name": agent.full_name,
                        "bio": agent.bio,
                        "location": agent.location,
                        "skills": agent.skills or []
                    }
                    
                    decision = await inference_service.decide_on_candidate(
                        agent_profile=agent_profile,
                        candidate_profile=candidate
                    )

                    # 4. Save Trace (Observability)
                    if decision:
                        trace = AgentTrace(
                            agent_id=agent.id,
                            interaction_type="SCREENING",
                            reasoning_log=decision.model_dump(), # Saves full JSON
                            decision=decision.decision
                        )
                        session.add(trace)
                        await session.commit()
                        
                        logger.info(f" Trace saved. Agent decided: {decision.decision}")

            except Exception as e:
                logger.error(f"Worker Error: {e}")

if __name__ == "__main__":
    worker = AgentWorker()
    asyncio.run(worker.start())