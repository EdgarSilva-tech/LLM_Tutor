from .la_settings import la_settings
import aio_pika
from aio_pika.abc import AbstractChannel
import json
import asyncio
from typing import Any, Dict
from .logging_config import get_logger
from .data_models import LearningAssessmentRequest, MasteryStore
from .model import learning_assessment_adviser
from fastapi import HTTPException
from datetime import datetime, timedelta
from sqlmodel import Session, select
from .db import engine

logger = get_logger(__name__)

EXCHANGE_NAME = la_settings.model_dump().get("RABBITMQ_EXCHANGE", "app.events")
ROUTING_KEY = la_settings.model_dump().get(
    "RABBITMQ_ROUTING_KEY", "evaluation.completed"
)
PREFETCH = int(la_settings.model_dump().get("RABBITMQ_PREFETCH", 16))
RABBIT_URL = la_settings.model_dump().get("RABBITMQ_URL")

QUEUE_NAME = "evaluation.completed.q"
DLX_NAME = "app.dlx"
DLQ_NAME = "evaluation.completed.dlq"
ACTION_TYPE_REMINDER = "reminder"
ACTION_TYPE_FOLLOW_UP_QUIZ = "quiz"
REMINDER_1_DELAY_DAYS = la_settings.LA_REMINDER_1_DELAY_DAYS
REMINDER_2_DELAY_DAYS = la_settings.LA_REMINDER_2_DELAY_DAYS
FOLLOW_UP_QUIZ_DELAY_DAYS = la_settings.LA_FOLLOW_UP_QUIZ_DELAY_DAYS


def _build_fixed_schedule(start_at: datetime) -> list[tuple[str, datetime]]:
    reminder_1_due_at = start_at + timedelta(days=REMINDER_1_DELAY_DAYS)
    reminder_2_due_at = reminder_1_due_at + timedelta(days=REMINDER_2_DELAY_DAYS)
    follow_up_quiz_due_at = reminder_2_due_at + timedelta(
        days=FOLLOW_UP_QUIZ_DELAY_DAYS
    )
    return [
        (ACTION_TYPE_REMINDER, reminder_1_due_at),
        (ACTION_TYPE_REMINDER, reminder_2_due_at),
        (ACTION_TYPE_FOLLOW_UP_QUIZ, follow_up_quiz_due_at),
    ]


async def _handle_message(message: aio_pika.IncomingMessage) -> None:
    async with message.process(requeue=False):
        payload: Dict[str, Any] = json.loads(message.body)
        msg = LearningAssessmentRequest(**payload)
        score = sum(msg.scores)
        now = datetime.now()
        mastery_band = "low" if score < 0.6 else "medium" if score < 0.8 else "high"
        schedule = _build_fixed_schedule(now)
        try:
            with Session(engine) as session:
                attempts = len(
                    session.exec(
                        select(MasteryStore).where(
                            MasteryStore.username == msg.username,
                            MasteryStore.topic == msg.topic,
                            MasteryStore.action_type == ACTION_TYPE_FOLLOW_UP_QUIZ,
                        )
                    ).all()
                )
                for action_type, due_at in schedule:
                    mastery = MasteryStore(
                        username=msg.username,
                        topic=msg.topic,
                        score=score,
                        attempts=attempts + 1,
                        rolling_avg=score / (attempts + 1),
                        last_quiz_id=msg.assessment_id,
                        updated_at=now,
                        mastery_band=mastery_band,
                        created_at=now,
                        status="pending",
                        action_type=action_type,
                        due_at=due_at,
                    )
                    session.add(mastery)
                session.commit()
        except Exception as e:
            logger.error(f"Error storing mastery: {e}")
            raise HTTPException(status_code=500, detail=f"Error storing mastery: {e}")
        logger.info(f"Consuming assessment: {msg}")
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
        raise HTTPException(
            status_code=500, detail=f"Error in learning assessment: {e}"
        )


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
            logger.error(f"Consumer stopped with error: {e}")

    task = asyncio.create_task(_runner())
    task.stop_event = stop_event  # type: ignore[attr-defined]
    return task
