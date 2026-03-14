import contextlib
from contextlib import asynccontextmanager

import aio_pika
from fastapi import FastAPI

from .consumer import start_consumer_task
from .data_models import EmailRequest, EmailResponse
from .email import send_email
from .logger import get_logger
from .settings import settings

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    consumer_task = start_consumer_task()
    try:
        yield
    finally:
        stop_event = getattr(consumer_task, "stop_event", None)
        if stop_event is not None:
            stop_event.set()
        consumer_task.cancel()
        with contextlib.suppress(Exception):
            await consumer_task
        logger.info("Notification consumer stopped")


app = FastAPI(title="Notification Service", lifespan=lifespan)


@app.post("/send-email", response_model=EmailResponse)
async def send_email_endpoint(email_request: EmailRequest) -> EmailResponse:
    return await send_email(email_request)


@app.get("/health")
async def health_check():
    rabbit = "disabled"
    try:
        if settings.RABBITMQ_URL:
            conn = await aio_pika.connect_robust(settings.RABBITMQ_URL)
            await conn.close()
            rabbit = "ok"
    except Exception:
        rabbit = "error"
    return {
        "status": "healthy",
        "service": "Notification Service",
        "rabbitmq": rabbit,
    }
