import aio_pika
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class RabbitMQClient:
    _connection = None
    _channel = None

    @classmethod
    async def get_connection(cls):
        if cls._connection is None or cls._connection.is_closed:
            logger.info("Connecting to RabbitMQ...")
            cls._connection = await aio_pika.connect_robust(
                settings.RABBITMQ_URL
            )
        return cls._connection

    @classmethod
    async def get_channel(cls):
        if cls._channel is None or cls._channel.is_closed:
            connection = await cls.get_connection()
            cls._channel = await connection.channel()
            # Important: Set QoS (Quality of Service)
            # This ensures a worker only gets 1 task at a time (Prevent overload)
            await cls._channel.set_qos(prefetch_count=1)
        return cls._channel

    @staticmethod
    async def publish(queue_name: str, message: dict):
        """
        Publish a JSON message to a specific queue.
        """
        import json
        
        channel = await RabbitMQClient.get_channel()
        
        # Ensure queue exists
        queue = await channel.declare_queue(queue_name, durable=True)
        
        await channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(message).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key=queue_name
        )

# Helper dependency
async def get_rabbitmq():
    return await RabbitMQClient.get_channel()