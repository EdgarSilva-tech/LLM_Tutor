import asyncio

import aio_pika
from aio_pika.abc import AbstractChannel, AbstractIncomingMessage
from aiormq.types import FieldTable

from .data_models import EmailRequest
from .email import send_email
from .logger import get_logger
from .settings import settings

EXCHANGE_NAME = settings.RABBITMQ_EXCHANGE
ROUTING_KEY = settings.RABBITMQ_ROUTING_KEY
PREFETCH = settings.RABBITMQ_PREFETCH
RABBIT_URL = settings.RABBITMQ_URL
DLQ_NAME = settings.RABBITMQ_DLQ_NAME
DLX_NAME = settings.RABBITMQ_DLX_NAME

QUEUE_NAME = settings.RABBITMQ_QUEUE_NAME

logger = get_logger(__name__)


async def _handle_message(message: AbstractIncomingMessage) -> None:
    async with message.process(requeue=False):
        email_request = EmailRequest.model_validate_json(message.body)
        logger.info("Received email request for %s", email_request.to)
        await handle_email_request(email_request)


async def handle_email_request(email_request: EmailRequest) -> None:
    response = await send_email(email_request)
    logger.info("Email response: %s", response)


async def _declare_topology(channel: AbstractChannel) -> None:
    # DLX/ DLQ
    dlx = await channel.declare_exchange(
        DLX_NAME, aio_pika.ExchangeType.TOPIC, durable=True
    )
    dlq = await channel.declare_queue(DLQ_NAME, durable=True)
    await dlq.bind(dlx, routing_key="#")

    # Main exchange/queue with DLX
    args: FieldTable = {"x-dead-letter-exchange": DLX_NAME}
    exchange = await channel.declare_exchange(
        EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True
    )
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
            logger.error("Notification consumer stopped with error: %s", e)

    task = asyncio.create_task(_runner())
    task.stop_event = stop_event  # type: ignore[attr-defined]
    return task
