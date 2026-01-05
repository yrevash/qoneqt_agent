import asyncio
import json
import logging
import aio_pika
from uuid import UUID
from sqlalchemy import select

from app.core.config import settings
from app.core.queue import RabbitMQClient
from app.core.database import AsyncSessionLocal
from app.modules.identity.models import User, AgentTrace, Connection  # <--- Import Connection
from app.modules.recsys.service import recsys_service
from app.modules.agent_brain.service import inference_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("qoneqt.worker")

class AgentWorker:
    async def start(self):
        connection = await RabbitMQClient.get_connection()
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)
        
        queue = await channel.declare_queue("queue.high_priority", durable=True)
        await queue.consume(self.process_message)
        logger.info("Agent Worker (SOTA Networking) Listening...")
        await asyncio.Future()

    async def process_message(self, message: aio_pika.IncomingMessage):
        async with message.process():
            try:
                payload = json.loads(message.body)
                agent_id_str = payload.get("agent_id")
                # 1. EXTRACT THE SPECIFIC GOAL
                user_query = payload.get("query", "General networking")
                trace_id = payload.get("trace_id")
                
                async with AsyncSessionLocal() as session:
                    agent = await session.get(User, UUID(agent_id_str))
                    if not agent: return

                    logger.info(f"Mission Start: {agent.full_name} wants '{user_query}'")

                    # 2. RUN RECSYS
                    recommendations = await recsys_service.get_recommendations(
                        initiator_id=agent.id,
                        query_text=user_query, # Use specific query for vector search
                        limit=3
                    )
                    
                    if not recommendations:
                        logger.info("No candidates found.")
                        return

                    for candidate_data in recommendations:
                        candidate_id = UUID(candidate_data['user_id'])
                        
                        # 3. STATE CHECK (The Anti-Spam Layer)
                        # Check if we already have a relationship
                        stmt = select(Connection).where(
                            Connection.initiator_id == agent.id,
                            Connection.receiver_id == candidate_id
                        )
                        existing_conn = await session.execute(stmt)
                        if existing_conn.scalars().first():
                            logger.info(f"Skipping {candidate_data['full_name']} (Already connected/pending)")
                            continue

                        # 4. THE BRAIN (Context-Aware)
                        decision = await inference_service.decide_on_candidate(
                            agent_profile={
                                "full_name": agent.full_name,
                                "bio": agent.bio,
                                "location": agent.location,
                                "skills": agent.skills
                            },
                            candidate_profile=candidate_data,
                            user_query=user_query 
                        )

                        if decision:
                            logger.info(f"Verdict on {candidate_data['full_name']}: {decision.decision}")
                            
                            # 5. ACTION & PERSISTENCE
                            # Save the Thought
                            trace = AgentTrace(
                                agent_id=agent.id,
                                target_id=candidate_id,
                                request_id=trace_id,
                                interaction_type="SCREENING",
                                reasoning_log=decision.model_dump(),
                                decision=decision.decision
                            )
                            session.add(trace)

                            # If Accepted, Create the Connection (State)
                            if decision.decision == "ACCEPT":
                                new_conn = Connection(
                                    initiator_id=agent.id,
                                    receiver_id=candidate_id,
                                    status="PENDING",
                                    request_id=trace_id
                                )
                                session.add(new_conn)
                                logger.info(f"Connection Request Sent to {candidate_data['full_name']}")
                            
                            await session.commit()

            except Exception as e:
                logger.error(f"Worker Error: {e}")

if __name__ == "__main__":
    worker = AgentWorker()
    asyncio.run(worker.start())