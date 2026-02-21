import json
import asyncio
import aio_pika
from typing import Any, Dict
from .logging_config import get_logger
from .la_settings import la_settings
from aio_pika.abc import AbstractRobustConnection, AbstractChannel
from typing import Optional


logger = get_logger(__name__)

EXCHANGE_NAME = la_settings.RABBITMQ_DELAYED_EXCHANGE
ROUTING_KEY = la_settings.RABBITMQ_ROUTING_KEY_GENERATE
PREFETCH = int(la_settings.RABBITMQ_PREFETCH)
RABBIT_URL = la_settings.RABBITMQ_URL


# Reutilização de ligação/canal + retry simples para reduzir falhas intermitentes
_connection: Optional[AbstractRobustConnection] | None = None
_channel: Optional[AbstractChannel] | None = None


async def _get_channel() -> AbstractChannel:
    global _connection, _channel
    if _connection is None or _connection.is_closed:
        # Aumenta timeout para lidar com arranques / flutuações de rede
        _connection = await aio_pika.connect_robust(
            RABBIT_URL,
            timeout=10,
            client_properties={"connection_name": "learning-assessment-quiz-publisher"},
        )
    if _channel is None or _channel.is_closed:
        _channel = await _connection.channel(publisher_confirms=True)

    assert _channel is not None
    return _channel


async def _publish(payload: Dict[str, Any], routing_key: str, delay: int = 0) -> None:
    channel = await asyncio.wait_for(_get_channel(), timeout=3.0)
    exchange = await channel.declare_exchange(
        la_settings.RABBITMQ_DELAYED_EXCHANGE,
        type="x-delayed-message",
        durable=True,
        arguments={"x-delayed-type": "topic"},
    )
    message = aio_pika.Message(
        body=json.dumps(payload).encode("utf-8"),
        content_type="application/json",
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        headers={"x-delay": delay}
    )
    await exchange.publish(message, routing_key=routing_key)
    logger.info(f"Quizz create request published: {payload}")


async def _publish_with_retry(
    payload: Dict[str, Any], routing_key: str, max_retries: int = 7, delay: int = 0
) -> None:
    for attempt in range(max_retries):
        try:
            await _publish(payload, routing_key, delay)
            return
        except Exception as e:
            logger.error(
                f"Quizz create request publish failed (attempt {attempt + 1}/{max_retries}): {e}"
            )
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2**attempt)
    raise Exception("Quizz create request publish failed after all retries")


def publish_quizz_create_request(payload: Dict[str, Any], delay: int = 0) -> None:
    asyncio.run(_publish_with_retry(payload, la_settings.RABBITMQ_ROUTING_KEY_GENERATE, delay=delay))