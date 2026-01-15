import json
import asyncio
import aio_pika
from typing import Any, Dict, List
from .logging_config import get_logger
from .data_models import EvaluationJobMessage
from .model import eval_answer
from .persistence import store_evals
from .cache import redis_client
from .eval_settings import eval_settings

logger = get_logger(__name__)

EXCHANGE_NAME = eval_settings.model_dump().get("RABBITMQ_EXCHANGE", "app.events")
ROUTING_KEY = eval_settings.model_dump().get(
    "RABBITMQ_ROUTING_KEY", "quiz.generate.request"
)
PREFETCH = int(eval_settings.model_dump().get("RABBITMQ_PREFETCH", 16))
RABBIT_URL = eval_settings.model_dump().get("RABBITMQ_URL")

QUEUE_NAME = "quiz.generate.q"
DLX_NAME = "app.dlx"
DLQ_NAME = "quiz.generate.dlq"


async def _handle_message(message: aio_pika.IncomingMessage) -> None:
    async with message.process(requeue=False):
        payload: Dict[str, Any] = json.loads(message.body)
        msg = EvaluationJobMessage(**payload)
        logger.info(f"Consuming job_id={msg.job_id} for user={msg.username}")

        feedback: List[Dict[str, Any]] = []
        for question, answer in zip(msg.quizz_questions, msg.student_answers or []):
            result = json.loads(eval_answer(question, answer).content)
            store_evals(
                msg.username,
                question,
                answer,
                result["correct_answer"],
                result["score"],
                result["feedback"],
            )
            feedback.append(
                {
                    "question": question,
                    "student_answer": answer,
                    "correct_answer": result["correct_answer"],
                    "feedback": result["feedback"],
                    "score": result["score"],
                }
            )

        # Persist aggregated feedback in Redis under Eval:{username}:{job_id}
        key = f"Eval:{msg.username}:{msg.job_id}"
        redis_client.set(key, json.dumps(feedback))
        logger.info(f"Stored feedback for job_id={msg.job_id} key={key}")


async def _declare_topology(channel: aio_pika.abc.AbstractChannel) -> None:
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
    # attach a stopper for external cancellation
    task.stop_event = stop_event  # type: ignore[attr-defined]
    return task
