import json
import asyncio
import aio_pika
from typing import Any, Dict
from quizz_settings import quizz_settings


async def publish_evaluation_request(payload: Dict[str, Any]) -> None:
    connection = await aio_pika.connect_robust(quizz_settings.RABBITMQ_URL)
    async with connection:
        channel = await connection.channel(publisher_confirms=True)
        exchange = await channel.declare_exchange(
            quizz_settings.RABBITMQ_EXCHANGE,
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )
        message = aio_pika.Message(
            body=json.dumps(payload).encode("utf-8"),
            content_type="application/json",
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        )
        await exchange.publish(message, routing_key=quizz_settings.RABBITMQ_ROUTING_KEY)


def publish_evaluation_request_sync(payload: Dict[str, Any]) -> None:
    asyncio.run(publish_evaluation_request(payload))
