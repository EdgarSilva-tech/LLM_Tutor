from fastapi import FastAPI, HTTPException
from .data_models import (
    LearningAssessmentRequest,
    MasteryScheduleResponse,
    ReminderRequest,
)
from .model import learning_assessment_adviser, reminder_generator
from .logging_config import get_logger
from contextlib import asynccontextmanager
from .db import create_db_and_tables
from .consumer import start_consumer_task
import contextlib
import asyncio
from .quizz_create_publish import publish_quizz_create_request
from .persistence import (
    get_learning_assessment_by_username,
    get_learning_assessment_mastery_by_username,
)


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


@app.post("/reminder")
async def reminder_service(request: ReminderRequest):
    """Reminder endpoint"""
    try:
        return reminder_generator(request.model_dump())
    except Exception as e:
        logger.error(f"Error in reminder service: {e}")
        raise HTTPException(status_code=500, detail=f"Error in reminder service: {e}")


@app.get("/learning-assessment/{username}")
async def get_learning_assessment(username: str):
    """Get learning assessment for a user"""
    try:
        return get_learning_assessment_by_username(username)
    except Exception as e:
        logger.error(f"Error in getting learning assessment for user: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error in getting learning assessment for user: {e}",
        )


@app.get(
    "/learning-assessment/{username}/mastery",
    response_model=MasteryScheduleResponse,
)
async def get_learning_assessment_mastery(username: str):
    """Get learning assessment mastery for a user"""
    try:
        return get_learning_assessment_mastery_by_username(username)
    except Exception as e:
        logger.error(f"Error in getting learning assessment mastery for user: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error in getting learning assessment mastery for user: {e}",
        )
