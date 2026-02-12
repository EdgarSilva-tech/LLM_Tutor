import asyncio
import aio_pika
from aio_pika.abc import AbstractRobustConnection, AbstractChannel
from typing import Any, Dict, Optional
from .quizz_settings import quizz_settings
import json
from .logging_config import get_logger

logger = get_logger(__name__)

# Reutilização de ligação/canal + retry simples para reduzir falhas intermitentes
_connection: Optional[AbstractRobustConnection] | None = None
_channel: Optional[AbstractChannel] | None = None


async def _get_channel() -> AbstractChannel:
    global _connection, _channel
    if _connection is None or _connection.is_closed:
        # Aumenta timeout para lidar com arranques / flutuações de rede
        _connection = await aio_pika.connect_robust(
            quizz_settings.RABBITMQ_URL,
            timeout=10,
            client_properties={"connection_name": "quizz-service-publisher"},
        )
    if _channel is None or _channel.is_closed:
        _channel = await _connection.channel(publisher_confirms=True)

    assert _channel is not None
    return _channel


async def _publish(payload: Dict[str, Any], routing_key: str) -> None:
    channel = await asyncio.wait_for(_get_channel(), timeout=3.0)
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
    await exchange.publish(message, routing_key=routing_key)
    logger.info(f"Evaluation completed published: {payload}")


async def _publish_with_retry(payload: Dict[str, Any], routing_key: str, max_retries: int = 7) -> None:
    for attempt in range(max_retries):
        try:
            await _publish(payload, routing_key)
            return
        except Exception as e:
            logger.error(f"Evaluation completed publish failed (attempt {attempt+1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)
    raise Exception("Evaluation completed publish failed after all retries")


def publish_evaluation_completed_sync(payload: Dict[str, Any]) -> None:
    asyncio.run(_publish_with_retry(payload, "evaluation.completed"))
