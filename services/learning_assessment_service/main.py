from fastapi import FastAPI, HTTPException
from .data_models import LearningAssessmentRequest
from .model import learning_assessment_adviser
from .logging_config import get_logger
from contextlib import asynccontextmanager
from .db import create_db_and_tables
from .consumer import start_consumer_task
import contextlib
import asyncio
from .quizz_create_publish import publish_quizz_create_request


logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Creating Learning Assessment tables...")
    create_db_and_tables()
    logger.info("Learning Assessment tables created. Service is ready.")
    consumer_task = start_consumer_task()
    try:
        yield
    finally:
        stop_event = getattr(consumer_task, "stop_event", None)
        if stop_event is not None:
            stop_event.set()
        consumer_task.cancel()
        with contextlib.suppress(Exception):
            asyncio.get_event_loop().run_until_complete(consumer_task)
        logger.info("Consumer task stopped")
    yield


app = FastAPI(title="Learning Assessment Service", lifespan=lifespan)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Learning Assessment Service"}


@app.post("/learning-assessment")
async def learning_assessment_service(request: LearningAssessmentRequest):
    """Learning assessment endpoint"""
    try:
        return learning_assessment_adviser(
            request.quizz_questions,
            request.student_answers,
            request.correct_answers,
            request.scores,
            request.feedback,
        )
        publish_quizz_create_request(request.model_dump())
    except Exception as e:
        logger.error(f"Error in learning assessment service: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error in learning assessment service: {e}"
        )
