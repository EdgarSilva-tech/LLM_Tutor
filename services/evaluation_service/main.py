from fastapi import FastAPI, Depends, HTTPException, status
from typing import Annotated
from .data_models import EvaluationRequest, User, SingleEvaluationRequest
from .model import eval_answer
import hashlib
import json
from .cache import redis_client
from .auth_client import get_current_active_user
from contextlib import asynccontextmanager
import contextlib
import asyncio
from .mq_consumer import start_consumer_task
from .eval_settings import eval_settings
import aio_pika
from .db import create_db_and_tables
from .logging_config import get_logger
from .persistence import store_evals
from typing import Tuple, List, cast

# Initialize the logger for this module
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Creating Evaluation tables...")
    create_db_and_tables()
    logger.info("Evaluation tables created. Service is ready.")
    consumer_task = start_consumer_task()
    try:
        yield
    finally:
        # Graceful stop
        stop_event = getattr(consumer_task, "stop_event", None)
        if stop_event is not None:
            stop_event.set()
        consumer_task.cancel()
        with contextlib.suppress(Exception):
            asyncio.get_event_loop().run_until_complete(consumer_task)


app = FastAPI(title="Evaluation Service", lifespan=lifespan)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    rabbit = "disabled"
    try:
        if eval_settings.RABBITMQ_URL:
            conn = await aio_pika.connect_robust(eval_settings.RABBITMQ_URL)
            await conn.close()
            rabbit = "ok"
    except Exception:
        rabbit = "error"
    return {
        "status": "healthy",
        "service": "Evaluation Service",
        "rabbitmq": rabbit,
    }


@app.post("/eval-service")
def evaluation(
    request: EvaluationRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    try:
        if request.quizz_questions:
            feedback = []
            question_list = request.quizz_questions
            logger.info(f"question_list: {question_list}")
            answer_list = request.student_answers
            logger.info(f"answer_list: {answer_list}")

            for question, answer in zip(question_list, answer_list):
                _resp = eval_answer(question, answer)
                _content = getattr(_resp, "content", _resp)
                correct_answer = json.loads(cast(str, _content))
                logger.info(f"correct_answer: {correct_answer}")
                # request.student_responses.append(request.student_response)
                store_evals(
                    current_user.username,
                    question,
                    answer,
                    correct_answer["correct_answer"],
                    correct_answer["score"],
                    correct_answer["feedback"],
                )

                feedback.append(
                    {
                        "question": question,
                        "student_answer": answer,
                        "correct_answer": correct_answer["correct_answer"],
                        "feedback": correct_answer["feedback"],
                        "score": correct_answer["score"],
                    }
                )

            question_str = json.dumps(feedback, sort_keys=True)
            question_hash = hashlib.sha256(question_str.encode()).hexdigest()
            key = f"Eval:{current_user.username}:{question_hash}"
            redis_client.set(key, question_str)
            logger.info(f"Feedback cached: {feedback}")

            return {"request_id": question_hash, "feedback": feedback}

    except Exception as e:
        logger.error(f"Evaluation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {str(e)}",
        )


@app.post("/eval-service/evaluate_answer")
def evaluate_answer(request: SingleEvaluationRequest):
    try:
        response = eval_answer(request.question, request.answer)
        logger.info(f"Question answered: {response}")
        return json.loads(cast(str, getattr(response, "content", response)))

    except Exception as e:
        logger.error(f"Evaluation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {str(e)}",
        )


@app.get("/eval-service/get-feedback")
def get_feedback(current_user: Annotated[User, Depends(get_current_active_user)]):
    matching_keys: list[str] = []
    cursor = 0  # Start with cursor 0

    # Scan until the cursor returned by Redis is 0
    while True:
        cursor, keys = cast(
            Tuple[int, List[str]],
            redis_client.scan(
                cursor=cursor, match=f"Eval:{current_user.username}:*", count=100
            ),
        )
        logger.info(f"Matching keys: {matching_keys}")
        matching_keys.extend(keys)
        if cursor == 0:
            break

    # Retrieve all the values for the found keys
    if matching_keys:
        values = redis_client.mget(matching_keys)
        logger.info(f"Values: {values}")
        return values
    else:
        return "No keys found for the pattern."


@app.get("/eval-service/jobs/{job_id}")
def get_job_status(
    job_id: str, current_user: Annotated[User, Depends(get_current_active_user)]
):
    key = f"Eval:{current_user.username}:{job_id}"
    val = redis_client.get(key)
    if not val:
        return {"status": "processing"}
    try:
        return {"status": "done", "feedback": json.loads(cast(str, val))}
    except Exception:
        return {"status": "done", "feedback": val}


# Protected endpoint to test authentication
@app.get("/eval-service/me")
async def get_my_info(current_user: Annotated[User, Depends(get_current_active_user)]):
    """Get current user info (for testing auth integration)"""
    return {
        "message": f"Hello {current_user.username}!",
        "user_info": current_user,
    }
