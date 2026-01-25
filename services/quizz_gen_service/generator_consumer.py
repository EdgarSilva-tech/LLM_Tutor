import json
import asyncio
import aio_pika
from typing import Any, Dict
from .logging_config import get_logger
from .quizz_settings import quizz_settings
from .cache import redis_client
from .model import quizz_generator
from aio_pika import abc as aio_abc
from aiormq.types import FieldTable

logger = get_logger(__name__)

EXCHANGE_NAME = quizz_settings.RABBITMQ_EXCHANGE
ROUTING_KEY = quizz_settings.RABBITMQ_ROUTING_KEY_GENERATE
PREFETCH = int(quizz_settings.RABBITMQ_PREFETCH)
RABBIT_URL = quizz_settings.RABBITMQ_URL

QUEUE_NAME = "quiz.create.q"
DLX_NAME = "app.dlx"
DLQ_NAME = "quiz.create.dlq"


async def _handle_message(message: aio_abc.AbstractIncomingMessage) -> None:
    async with message.process(requeue=False):
        payload: Dict[str, Any] = json.loads(message.body)
        username = payload.get("username")
        quiz_id = payload.get("quiz_id")
        topic = payload.get("topic")
        num_questions = int(payload.get("num_questions", 3))
        difficulty = payload.get("difficulty")
        style = payload.get("style")
        if not (username and quiz_id and topic and difficulty and style):
            logger.error("Invalid payload for quiz generation: %s", payload)
            return

        key = f"Quiz:{username}:{quiz_id}"
        # Mark as processing
        redis_client.setex(key, 3600, json.dumps({"status": "processing"}))
        last_error: Exception | None = None
        backoff = 0.5
        for attempt in range(3):
            try:
                questions = quizz_generator(topic, num_questions, difficulty, style)
                redis_client.setex(
                    key,
                    3600,
                    json.dumps({"status": "done", "questions": questions}),
                )
                logger.info(
                    "Quiz generated and stored: %s (attempt=%d)", key, attempt + 1
                )
                break
            except Exception as e:
                last_error = e
                logger.warning("Quiz generation attempt %d failed: %s", attempt + 1, e)
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 5.0)
        else:
            # All attempts failed
            logger.exception("Quiz generation failed after retries: %s", last_error)
            redis_client.setex(
                key, 1800, json.dumps({"status": "failed", "error": str(last_error)})
            )


async def _declare_topology(channel: aio_abc.AbstractChannel) -> None:
    # DLX/ DLQ
    dlx = await channel.declare_exchange(
        DLX_NAME, aio_pika.ExchangeType.TOPIC, durable=True
    )
    dlq = await channel.declare_queue(DLQ_NAME, durable=True)
    await dlq.bind(dlx, routing_key="#")

    # Main exchange/queue with DLX
    exchange = await channel.declare_exchange(
        EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True
    )
    args: FieldTable = {"x-dead-letter-exchange": DLX_NAME}
    queue = await channel.declare_queue(QUEUE_NAME, durable=True, arguments=args)
    await queue.bind(exchange, routing_key=ROUTING_KEY)


async def run_consumer(stop_event: asyncio.Event) -> None:
    assert RABBIT_URL, "RABBITMQ_URL must be set"
    connection = await aio_pika.connect_robust(RABBIT_URL)
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=PREFETCH)
        await _declare_topology(channel)
        queue = await channel.get_queue(QUEUE_NAME, ensure=False)
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                if stop_event.is_set():
                    break
                await _handle_message(message)


def start_consumer_task() -> asyncio.Task:
    stop_event = asyncio.Event()

    async def _runner():
        try:
            await run_consumer(stop_event)
        except Exception as e:
            logger.error("Quiz generator consumer stopped with error: %s", e)

    task = asyncio.create_task(_runner())
    task.stop_event = stop_event  # type: ignore[attr-defined]
    return task
