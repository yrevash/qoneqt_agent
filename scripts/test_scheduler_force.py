import asyncio
import sys
import os
import time
from redis.asyncio import Redis

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import settings
from app.modules.scheduler.time_engine import TimeEngine

async def force_schedule_test():
    print("Initializing Scheduler Test...")
    
    # 1. Connect to Redis directly
    redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    
    # 2. Pick a victim (Alice Rust's ID from seed_db.py)
    # If you changed her ID, grab a real one from your DB or logs
    # For now, we'll assume the one we generated or just use a dummy to see the log
    target_agent_id = "acc52e5d-83ef-4e40-a1f2-e0cc4d98afab" 
    
    print(f"   Injecting 'Wake Up' task for Agent {target_agent_id}...")
    
    # 3. Insert into the Schedule Key with a timestamp in the PAST (so it's due NOW)
    # Score = Timestamp (Now - 60 seconds)
    overdue_timestamp = time.time() - 60
    await redis.zadd("scheduler:queue", {target_agent_id: overdue_timestamp})
    
    print("   ✅ Task injected! It is now 'Overdue'.")
    
    # Check what's in the queue before processing
    queue_size = await redis.zcard("scheduler:queue")
    print(f"   📊 Scheduler queue size: {queue_size}")
    
    print("   🚀 Starting TimeEngine Ticker (Ctrl+C to stop)...")
    print("   (Watch for 'Processing 1 due agents' below)")
    print("-" * 50)

    # 4. Run the actual Engine Logic
    engine = TimeEngine()
    
    # Run just one tick to see what happens
    try:
        # Fetch due agents (just like the ticker loop does)
        now_ts = time.time()
        due_agents = await redis.zrangebyscore(
            "scheduler:queue",
            min=0,
            max=now_ts,
            start=0,
            num=50
        )
        
        print(f"   🔍 Found {len(due_agents)} due agents: {due_agents}")
        
        if due_agents:
            # Process them
            await engine._process_due_agents(due_agents)
            
            # Remove from Redis (like ticker does)
            await redis.zrem("scheduler:queue", *due_agents)
            
            print("\n" + "=" * 50)
            print("   ✅ Processing complete!")
        else:
            print("\n" + "=" * 50)
            print("   ⚠️ No due agents found (this shouldn't happen!)")
        
        # Check queue after
        queue_after = await redis.zcard("scheduler:queue")
        print(f"   📊 Queue size after processing: {queue_after}")
        
        # Check if any tasks were created (look in RabbitMQ queues via Redis)
        # Note: RabbitMQ queues aren't in Redis, so we'll check the high/low priority queues
        print(f"\n   📮 Tasks sent to RabbitMQ:")
        print(f"      - Check 'docker logs qoneqt_agent-worker-1' to see if tasks were picked up")
        print(f"      - Or run: docker exec qoneqt_agent-rabbitmq-1 rabbitmqctl list_queues")
        
        print("\n   💡 Next steps:")
        print("      - Check worker logs: docker logs -f qoneqt_agent-worker-1")
        print("      - Check database for new connection records")
        print("      - Monitor RabbitMQ: docker exec qoneqt_agent-rabbitmq-1 rabbitmqctl list_queues")
        print("=" * 50)
        
    except Exception as e:
        print(f"   ❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()
    
    await redis.aclose()

if __name__ == "__main__":
    try:
        asyncio.run(force_schedule_test())
    except KeyboardInterrupt:
        print("\n Test Stopped.")