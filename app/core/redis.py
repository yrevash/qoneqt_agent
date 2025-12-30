import redis.asyncio as redis
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
        """
        Cost Governor: Get current energy balance.
        """
        redis_conn = RedisClient.get_instance()
        balance = await redis_conn.get(f"user:energy:{user_id}")
        return int(balance) if balance else 0

    @staticmethod
    async def deduct_energy(user_id: str, amount: int):
        """
        Cost Governor: Deduct energy after inference.
        """
        redis_conn = RedisClient.get_instance()
        await redis_conn.decrby(f"user:energy:{user_id}", amount)

# Helper to get redis in dependencies
async def get_redis():
    return RedisClient.get_instance()