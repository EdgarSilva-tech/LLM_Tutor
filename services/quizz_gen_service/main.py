from fastapi import FastAPI, Depends, HTTPException, status
from typing import Annotated
from cache import redis_client
from model import quizz_generator
from data_models import QuizzRequest, User, SubmitAnswers
import hashlib
import json
from auth_client import get_current_active_user
from logging_config import get_logger
import uuid
from datetime import datetime
from mq import publish_evaluation_request_sync
from quizz_settings import quizz_settings

# Initialize the logger for this module
logger = get_logger(__name__)

app = FastAPI(title="Quiz Generation Service")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    rabbit = "disabled"
    try:
        if quizz_settings.RABBITMQ_URL:
            import aio_pika  # local import to avoid startup hard dep
            conn = await aio_pika.connect_robust(quizz_settings.RABBITMQ_URL)
            await conn.close()
            rabbit = "ok"
    except Exception:
        rabbit = "error"
    return {
        "status": "healthy",
        "service": "Quiz Generation Service",
        "rabbitmq": rabbit,
    }


@app.post("/generate-quiz")
def generate_quizz(
    request: QuizzRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    try:
        quizz = quizz_generator(
            request.topic,
            request.num_questions,
            request.difficulty,
            request.style,
        )
        logger.info(f"Quizz generated: {quizz}")
        quizz_str = json.dumps(
            {"questions": quizz},
            sort_keys=True,
        )
        quizz_hash = hashlib.sha256(
            quizz_str.encode()
        ).hexdigest()
        cache_key = f"quizz_request:{current_user.username}:{quizz_hash}"
        redis_client.set(cache_key, quizz_str)
        logger.info(
            f"Quizz cached: {quizz_str}, key: {cache_key}"
        )

        return {"quizz_questions": quizz}

    except Exception as e:
        logger.error(f"Quizz generation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quizz generation failed: {str(e)}",
        )


@app.post("/create-quiz")
def create_quiz(
    request: QuizzRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    try:
        questions = quizz_generator(
            request.topic,
            request.num_questions,
            request.difficulty,
            request.style,
        )
        quiz_id = str(uuid.uuid4())
        key = f"Quiz:{current_user.username}:{quiz_id}"
        # keep for 1 hour
        redis_client.setex(key, 3600, json.dumps(questions))
        return {"quiz_id": quiz_id, "questions": questions}
    except Exception as e:
        logger.error(f"Create quiz failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Create quiz failed: {str(e)}",
        )


@app.post("/submit-answers", status_code=202)
def submit_answers(
    payload: SubmitAnswers,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    try:
        key = f"Quiz:{current_user.username}:{payload.quiz_id}"
        data = redis_client.get(key)
        if not data:
            raise HTTPException(
                status_code=404,
                detail="Quiz not found or expired",
            )
        questions: list[str] = json.loads(data)
        if len(payload.answers) != len(questions):
            raise HTTPException(
                status_code=400,
                detail="Answers count mismatch",
            )

        job_id = str(uuid.uuid4())
        publish_evaluation_request_sync(
            {
                "job_id": job_id,
                "username": current_user.username,
                "student_id": current_user.username,
                "quizz_questions": questions,
                "student_answers": payload.answers,
                "created_at": datetime.utcnow().isoformat(),
            }
        )
        return {"job_id": job_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Submit answers failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Submit answers failed: {str(e)}",
        )


@app.post("/generate-async", status_code=202)
def generate_quizz_async(
    request: QuizzRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    try:
        quizz = quizz_generator(
            request.topic,
            request.num_questions,
            request.difficulty,
            request.style,
        )
        questions = quizz
        job_id = str(uuid.uuid4())
        payload = {
            "job_id": job_id,
            "username": current_user.username,
            "student_id": current_user.username,
            "quizz_questions": questions,
            "student_answers": [],
            "created_at": datetime.utcnow().isoformat(),
        }
        publish_evaluation_request_sync(payload)
        logger.info(
            "Published evaluation job job_id=%s user=%s",
            job_id,
            current_user.username,
        )
        return {"job_id": job_id}
    except Exception as e:
        logger.error(f"Quizz async publish failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quizz async publish failed: {str(e)}",
        )


@app.get("/get-quizz-questions")
def get_questions(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    try:
        matching_keys = []
        cursor = "0"  # Start with cursor 0

        # Scan until the cursor returned by Redis is 0
        while cursor != 0:
            cursor, keys = redis_client.scan(
                cursor=cursor,
                match=f"quizz_request:{current_user.username}:*",
                count=100,
            )
            matching_keys.extend(keys)

        # Retrieve all the values for the found keys
        if matching_keys:
            values = redis_client.mget(matching_keys)
            logger.info(f"Values: {values}")
            return values
        else:
            logger.info("No keys found for the pattern.")
            return "No keys found for the pattern."

    except Exception as e:
        logger.error(f"Failed to get quizz questions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get quizz questions: {str(e)}",
        )
