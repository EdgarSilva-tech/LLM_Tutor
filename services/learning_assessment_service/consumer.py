from .la_settings import la_settings
import aio_pika
from aio_pika.abc import AbstractChannel
import json
import asyncio
from typing import Any, Dict
from .logging_config import get_logger
from .data_models import LearningAssessmentRequest
from .model import learning_assessment_adviser
from fastapi import HTTPException

logger = get_logger(__name__)

EXCHANGE_NAME = la_settings.model_dump().get("RABBITMQ_EXCHANGE", "app.events")
ROUTING_KEY = la_settings.model_dump().get("RABBITMQ_ROUTING_KEY", "evaluation.completed")
PREFETCH = int(la_settings.model_dump().get("RABBITMQ_PREFETCH", 16))
RABBIT_URL = la_settings.model_dump().get("RABBITMQ_URL")

QUEUE_NAME = "evaluation.completed.q"
DLX_NAME = "app.dlx"
DLQ_NAME = "evaluation.completed.dlq"


async def _handle_message(message: aio_pika.IncomingMessage) -> None:
    async with message.process(requeue=False):
        payload: Dict[str, Any] = json.loads(message.body)
        msg = LearningAssessmentRequest(**payload)
        logger.info(f"Consuming assessment_id={msg.assessment_id}")
        await handle_learning_assessment(msg)


async def _declare_topology(channel: AbstractChannel) -> None:
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
    args = {"x-dead-letter-exchange": DLX_NAME}
    queue = await channel.declare_queue(QUEUE_NAME, durable=True, arguments=args)
    await queue.bind(exchange, routing_key=ROUTING_KEY)


async def handle_learning_assessment(msg: LearningAssessmentRequest) -> None:
    try:
        response = learning_assessment_adviser(
            msg.quizz_questions,
            msg.student_answers,
            msg.correct_answers,
            msg.scores,
            msg.feedback,
        )
        logger.info(f"Learning assessment response: {response}")
    except Exception as e:
        logger.error(f"Error in learning assessment: {e}")
        raise HTTPException(status_code=500, detail=f"Error in learning assessment: {e}")


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


async def start_consumer_task() -> asyncio.Task:
    stop_event = asyncio.Event()

    async def _runner():
        try:
            await run_consumer(stop_event)
        except Exception as e:
            logger.error(f"Consumer stopped with error: {e}")
    task = asyncio.create_task(_runner())
    task.stop_event = stop_event  # type: ignore[attr-defined]
    return task
