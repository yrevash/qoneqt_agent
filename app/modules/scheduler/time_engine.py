import asyncio
import logging
import random
import time
from datetime import datetime, timedelta, timezone
from typing import List
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.redis import RedisClient
from app.core.queue import RabbitMQClient
from app.modules.identity.models import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("qoneqt.scheduler")

REDIS_KEY_SCHEDULE = "scheduler:queue"
RABBITMQ_QUEUE_TASKS = "tasks.agent_wakeup"

class TimeEngine:
    """
    Layer 4: The Time Engine.
    Manages the lifecycle of Agent wake-ups using Probabilistic Scheduling.
    """

    async def start(self):
        """
        Main Entry Point. Starts both the Planner and Ticker loops concurrently.
        """
        logger.info(" Time Engine Starting...")
        
        # We run these as concurrent async tasks
        await asyncio.gather(
            self.run_planner_loop(),
            self.run_ticker_loop()
        )

    # -------------------------------------------------------------------------
    # 1. THE PLANNER (Batch Scheduler)
    # -------------------------------------------------------------------------
    async def run_planner_loop(self):
        """
        Runs continuously, but effectively acts on hourly/10-min boundaries.
        In production, this might be a separate CronJob, but a loop works for daemon mode.
        """
        logger.info("Planner Loop Initiated.")
        
        while True:
            try:
                # Run planning logic
                await self._plan_agent_activities()
                
                # Sleep for 10 minutes before checking if we need to plan again
                # (Real logic would calculate time until next hour, simplified here)
                await asyncio.sleep(600) 
                
            except Exception as e:
                logger.error(f" Planner Error: {e}")
                await asyncio.sleep(60) # Backoff on error

    async def _plan_agent_activities(self):
        """
        Scans DB for active agents and schedules them based on probability.
        """
        now = datetime.now(timezone.utc)
        current_hour = now.hour
        
        # Check if we already planned for this hour? (Optimization for later)
        # For now, we assume this runs cleanly.

        logger.info(f"Planning batch for Hour: {current_hour}:00")

        async with AsyncSessionLocal() as session:
            # Fetch all active agents
            # PRODUCTION NOTE: Use yield_per(1000) for massive datasets to avoid RAM OOM.
            stmt = select(User).where(User.is_active == True)
            result = await session.execute(stmt)
            agents = result.scalars().all()

            scheduled_count = 0
            redis = RedisClient.get_instance()

            async with redis.pipeline() as pipe:
                for agent in agents:
                    # 1. Get Probability for Current Hour
                    # Default to 0.0 if schedule is missing or malformed
                    if not agent.activity_schedule or len(agent.activity_schedule) != 24:
                        prob = 0.1 # Fallback: 10% chance
                    else:
                        prob = agent.activity_schedule[current_hour]

                    # 2. The Dice Roll (Leaky Bucket)
                    if random.random() < prob:
                        # 3. Calculate Jitter (Random minute/second within the next hour)
                        # We want them to wake up sometime in the next 60 mins.
                        delay_seconds = random.randint(0, 3600)
                        wake_time = now.timestamp() + delay_seconds
                        
                        # 4. Schedule in Redis ZSET
                        # Score = Timestamp, Member = AgentID
                        pipe.zadd(REDIS_KEY_SCHEDULE, {str(agent.id): wake_time})
                        scheduled_count += 1
                
                # Execute Batch Write
                await pipe.execute()

            if scheduled_count > 0:
                logger.info(f" Scheduled {scheduled_count}/{len(agents)} agents for action.")

    # -------------------------------------------------------------------------
    # 2. THE TICKER (Real-time Trigger)
    # -------------------------------------------------------------------------
    async def run_ticker_loop(self):
        """
        Polls Redis every second for tasks that are due.
        """
        logger.info(" Ticker Loop Initiated.")
        redis = RedisClient.get_instance()
        
        while True:
            try:
                now_ts = time.time()
                
                # 1. Fetch Due Tasks (Score <= Now)
                # ZRANGEBYSCORE key -inf +inf ...
                due_agents = await redis.zrangebyscore(
                    REDIS_KEY_SCHEDULE, 
                    min=0, 
                    max=now_ts, 
                    start=0, 
                    num=50  # Process in batches of 50 to prevent blocking
                )

                if due_agents:
                    logger.info(f"⚡ Waking up {len(due_agents)} agents...")
                    
                    # 2. Push to RabbitMQ
                    for agent_id in due_agents:
                        payload = {
                            "agent_id": agent_id,
                            "action": "WAKE_UP",
                            "timestamp": now_ts,
                            "reason": "scheduled_activity"
                        }
                        
                        # Publish to Queue (Persistent)
                        await RabbitMQClient.publish(
                            queue_name=RABBITMQ_QUEUE_TASKS,
                            message=payload
                        )

                    # 3. Cleanup Redis (Remove processed tasks)
                    # We remove strictly the ones we fetched
                    await redis.zrem(REDIS_KEY_SCHEDULE, *due_agents)

                # Wait for next tick
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Ticker Error: {e}")
                await asyncio.sleep(5)

if __name__ == "__main__":
    # Allow running this file directly to start the engine
    engine = TimeEngine()
    asyncio.run(engine.start())