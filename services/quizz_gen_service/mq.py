import json
import asyncio
import aio_pika
from typing import Any, Dict, Optional
from quizz_settings import quizz_settings

# Reutilização de ligação/canal + retry simples para reduzir falhas intermitentes
_connection: Optional[aio_pika.RobustConnection] = None
_channel: Optional[aio_pika.RobustChannel] = None


async def _get_channel() -> aio_pika.RobustChannel:
    global _connection, _channel
    if _connection is None or _connection.is_closed:
        _connection = await aio_pika.connect_robust(
            quizz_settings.RABBITMQ_URL,
            timeout=5,
            client_properties={"connection_name": "quizz-service-publisher"},
        )
    if _channel is None or _channel.is_closed:
        _channel = await _connection.channel(publisher_confirms=True)
    return _channel


async def _publish(payload: Dict[str, Any], routing_key: str) -> None:
    # Limita o tempo de espera para obter canal (falha rápida em caso de rede)
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


async def _publish_with_retry(
    payload: Dict[str, Any], routing_key: str, max_retries: int = 3
) -> None:
    last_error: Optional[Exception] = None
    for attempt in range(max_retries):
        try:
            await _publish(payload, routing_key)
            return
        except Exception as e:
            last_error = e
            # tenta reconectar e aplicar backoff exponencial
            try:
                if _connection and not _connection.is_closed:
                    await _connection.close()
            except Exception:
                pass
            await asyncio.sleep(0.2 * (2**attempt))
    if last_error:
        raise last_error


def publish_evaluation_request_sync(payload: Dict[str, Any]) -> None:
    asyncio.run(_publish_with_retry(payload, quizz_settings.RABBITMQ_ROUTING_KEY))


def publish_quiz_generate_request_sync(payload: Dict[str, Any]) -> None:
    asyncio.run(_publish_with_retry(payload, quizz_settings.RABBITMQ_ROUTING_KEY_GENERATE))
