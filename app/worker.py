import asyncio
import json
import logging
import aio_pika
from uuid import UUID

from app.core.config import settings
from app.core.queue import RabbitMQClient
from app.modules.recsys.service import recsys_service
from app.modules.identity.models import User
from app.core.database import AsyncSessionLocal

# Configure Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("qoneqt.worker")

class AgentWorker:
    """
    Layer 2: The Agent Worker.
    Consumes tasks from RabbitMQ and executes the 'Brain' logic.
    """

    async def start(self):
        """
        Connects to RabbitMQ and starts listening on multiple queues.
        """
        logger.info(" Agent Worker Starting...")
        connection = await RabbitMQClient.get_connection()
        channel = await connection.channel()
        
        # Set QoS to process 1 task at a time per worker instance (Prevent overload)
        await channel.set_qos(prefetch_count=1)

        # Listen to both High and Low priority queues
        queues = ["queue.high_priority", "queue.low_priority"]
        
        for q_name in queues:
            queue = await channel.declare_queue(q_name, durable=True)
            await queue.consume(self.process_message)
            logger.info(f"👂 Listening on {q_name}")

        # Keep running
        await asyncio.Future()

    async def process_message(self, message: aio_pika.IncomingMessage):
        """
        The Core Logic: Wake Up -> Context Load -> RecSys -> Action
        """
        async with message.process():
            try:
                payload = json.loads(message.body)
                agent_id_str = payload.get("agent_id")
                tier = payload.get("tier", "free")
                
                logger.info(f" Agent Waking Up: {agent_id_str} (Tier: {tier})")
                
                # 1. LOAD CONTEXT (Who am I?)
                agent_id = UUID(agent_id_str)
                async with AsyncSessionLocal() as session:
                    agent = await session.get(User, agent_id)
                    if not agent:
                        logger.error(f"Agent {agent_id} not found in DB.")
                        return

                    # 2. RUN RECSYS (Who should I talk to?)
                    # We use the implicit context of the agent (Location, etc.)
                    recommendations = await recsys_service.get_recommendations(
                        initiator_id=agent.id,
                        query_text="Find me relevant connections", # Default goal
                        limit=3,
                        enable_smart_location=True
                    )
                    
                    if recommendations:
                        top_match = recommendations[0]
                        match_name = top_match['full_name']
                        score = top_match['match_score']
                        
                        logger.info(f"  Insight: Found {len(recommendations)} candidates.")
                        logger.info(f"   Top Match: {match_name} (Score: {score})")
                        
                        # 3. TAKE ACTION (Simulated for Phase 4)
                        # In Phase 5, this is where we call vLLM to generate a message.
                        # For now, we log the 'Intent'.
                        logger.info(f"    ACTION: Would send Hello to {match_name}")
                    else:
                        logger.info("   💤 No relevant matches found. Going back to sleep.")

            except Exception as e:
                logger.error(f" Worker Error: {e}")

if __name__ == "__main__":
    worker = AgentWorker()
    asyncio.run(worker.start())