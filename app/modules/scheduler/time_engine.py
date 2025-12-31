import asyncio
import logging
import random
import time
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.redis import RedisClient
from app.core.queue import RabbitMQClient
from app.modules.identity.models import User

# Configure Structured Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("qoneqt.scheduler")

# CONSTANTS
REDIS_KEY_SCHEDULE = "scheduler:queue"
QUEUE_HIGH_PRIORITY = "queue.high_priority"
QUEUE_LOW_PRIORITY = "queue.low_priority"

class TimeEngine:
    """
    Layer 4: The Time Engine (Production V2).
    Implements Hybrid Priority Scheduling:
    - Track A: Trigger-Based (Handled via API Gateway)
    - Track B: Deterministic (Tier-Based Interval)
    - Track C: Background (Low Priority Filler)
    """

    async def start(self):
        """
        Main Entry Point. Starts Planner and Ticker concurrently.
        """
        logger.info(" Time Engine (Production Tier) Starting...")
        await asyncio.gather(
            self.run_planner_loop(),
            self.run_ticker_loop()
        )

    # -------------------------------------------------------------------------
    # 1. THE PLANNER (Tier-Based Scheduling)
    # -------------------------------------------------------------------------
    async def run_planner_loop(self):
        """
        Runs continuously. Plans the next hour's activities.
        """
        logger.info("Planner Loop Initiated.")
        
        while True:
            try:
                # Calculate time until next planning window (Start of next hour)
                now = datetime.now(timezone.utc)
                next_run = (now + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
                sleep_seconds = (next_run - now).total_seconds()
                
                # Execute Planning Logic
                await self._plan_agent_activities(now.hour)
                
                logger.info(f"Planner sleeping for {int(sleep_seconds)}s until next cycle...")
                await asyncio.sleep(sleep_seconds)
                
            except Exception as e:
                logger.error(f"Planner Error: {e}")
                await asyncio.sleep(60) # Safety backoff

    async def _plan_agent_activities(self, current_hour: int):
        """
        Scans DB and schedules agents based on Tier and Active Hours.
        """
        logger.info(f"Planning batch for Hour: {current_hour}:00")

        async with AsyncSessionLocal() as session:
            # Optimization: Fetch only active users
            stmt = select(User).where(User.is_active == True)
            result = await session.execute(stmt)
            agents = result.scalars().all()

            scheduled_count = 0
            redis = RedisClient.get_instance()

            async with redis.pipeline() as pipe:
                for agent in agents:
                    # 1. Check if Agent is "Awake" (Based on Bio-Rhythm)
                    # We assume 0.0 in schedule means "Deep Sleep" (Do not disturb)
                    schedule = agent.activity_schedule or [0.1] * 24
                    if len(schedule) != 24: schedule = [0.1] * 24
                    
                    if schedule[current_hour] <= 0.0:
                        continue # Skip sleeping agents

                    # 2. DETERMINISTIC TIER LOGIC
                    # TODO: In future, fetch 'tier' from DB. For now, we mock logic.
                    # Assumption: We define 'Pro' users logic dynamically or via a future column.
                    # Let's assume 'tier' is a property we will add. For now, everyone is 'Free'
                    # unless we hardcode specific IDs or logic.
                    
                    is_pro = False # Change this to `agent.tier == 'pro'` after migration
                    
                    should_schedule = False

                    if is_pro:
                        # PRO TIER: Schedule EVERY hour they are active.
                        should_schedule = True
                    else:
                        # FREE TIER: Schedule only every 6 hours (0, 6, 12, 18)
                        # This saves 80% of compute costs.
                        if current_hour % 6 == 0:
                            should_schedule = True
                        
                        # "Serendipity" Fallback (Track C):
                        # Give Free users a small random chance (10%) to wake up off-schedule
                        # to keep the network feeling alive.
                        elif random.random() < 0.10:
                            should_schedule = True

                    if should_schedule:
                        # 3. Apply Jitter (Spread load across the hour)
                        # We don't want 10k agents firing at Minute 0.
                        delay_seconds = random.randint(0, 3500) # 0 to 58 mins
                        wake_timestamp = time.time() + delay_seconds
                        
                        # Store in Redis: Score=Timestamp, Member=AgentID
                        pipe.zadd(REDIS_KEY_SCHEDULE, {str(agent.id): wake_timestamp})
                        scheduled_count += 1
                
                await pipe.execute()

            logger.info(f"✅ Scheduled {scheduled_count}/{len(agents)} agents (Tier-Adjusted).")

    # -------------------------------------------------------------------------
    # 2. THE TICKER (Priority Routing)
    # -------------------------------------------------------------------------
    async def run_ticker_loop(self):
        """
        High-frequency loop. Moves tasks from Redis -> RabbitMQ (Specific Queues).
        """
        logger.info(" Ticker Loop Initiated.")
        redis = RedisClient.get_instance()
        
        while True:
            try:
                now_ts = time.time()
                
                # 1. Fetch Due Tasks
                due_agents = await redis.zrangebyscore(
                    REDIS_KEY_SCHEDULE, 
                    min=0, 
                    max=now_ts, 
                    start=0, 
                    num=50 
                )

                if due_agents:
                    await self._process_due_agents(due_agents)
                    
                    # Remove processed tasks from Redis
                    await redis.zrem(REDIS_KEY_SCHEDULE, *due_agents)

                await asyncio.sleep(1) # Tick frequency

            except Exception as e:
                logger.error(f" Ticker Error: {e}")
                await asyncio.sleep(5)

    async def _process_due_agents(self, agent_ids: List[str]):
        """
        Routes agents to the correct Priority Queue based on Tier.
        """
        logger.info(f"⚡ Processing {len(agent_ids)} due agents...")
        
        # We need to fetch agents again to check their Tier for routing
        # (Redis only had the ID).
        async with AsyncSessionLocal() as session:
            stmt = select(User).where(User.id.in_(agent_ids))
            result = await session.execute(stmt)
            agents = result.scalars().all()
            
            for agent in agents:
                # 1. Determine Priority
                # TODO: Replace with `agent.tier`
                is_pro = False 
                
                target_queue = QUEUE_HIGH_PRIORITY if is_pro else QUEUE_LOW_PRIORITY
                
                payload = {
                    "agent_id": str(agent.id),
                    "action": "WAKE_UP",
                    "timestamp": time.time(),
                    "tier": "pro" if is_pro else "free",
                    "source": "scheduler"
                }

                # 2. Publish to RabbitMQ
                await RabbitMQClient.publish(
                    queue_name=target_queue,
                    message=payload
                )
                
                # logger.info(f"   -> Pushed {agent.full_name} to {target_queue}")

if __name__ == "__main__":
    # Allow running this file directly to start the engine
    engine = TimeEngine()
    asyncio.run(engine.start())