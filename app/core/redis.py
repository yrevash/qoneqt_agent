import redis.asyncio as redis
from typing import List
from app.core.config import settings

class RedisClient:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = redis.from_url(
                settings.REDIS_URL, 
                encoding="utf-8", 
                decode_responses=True
            )
        return cls._instance

    @staticmethod
    async def check_energy(user_id: str) -> int:
        redis_conn = RedisClient.get_instance()
        balance = await redis_conn.get(f"user:energy:{user_id}")
        return int(balance) if balance else 0

    @staticmethod
    async def deduct_energy(user_id: str, amount: int):
        redis_conn = RedisClient.get_instance()
        await redis_conn.decrby(f"user:energy:{user_id}", amount)

    @staticmethod
    async def get_follower_counts(user_ids: List[str]) -> List[int]:
        """
        Efficiently fetches follower counts for a list of users using a Pipeline.
        Returns a list of integers in the same order as user_ids.
        """
        if not user_ids:
            return []
            
        redis_conn = RedisClient.get_instance()
        async with redis_conn.pipeline() as pipe:
            for uid in user_ids:
                # Assuming the key schema is 'graph:followers:{uuid}' (Set)
                pipe.scard(f"graph:followers:{uid}")
            
            # Execute all commands in one network round-trip
            results = await pipe.execute()
            
        return [int(count) if count else 0 for count in results]

async def get_redis():
    return RedisClient.get_instance()