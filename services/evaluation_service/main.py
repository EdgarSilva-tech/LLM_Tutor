from fastapi import FastAPI, Depends, HTTPException, status
from typing import Annotated
from datetime import datetime
from sqlmodel import Session
from data_models import (
    Evaluation, EvaluationRequest, User, SingleEvaluationRequest
    )
from model import eval_answer
import hashlib
import json
from cache import redis_client
from auth_client import get_current_active_user
from contextlib import asynccontextmanager
from db import create_db_and_tables, engine
from logging_config import get_logger

# Initialize the logger for this module
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Creating Evaluation tables...")
    create_db_and_tables()
    logger.info("Evaluation tables created. Service is ready.")
    yield

app = FastAPI(title="Evaluation Service", lifespan=lifespan)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Evaluation Service"}


def store_evals(question: str, answer: str, correct_answer: str,
                score: float, feedback: str, username: str):

    with Session(engine) as session:
        try:
            eval = Evaluation(username=username.username,
                              question=question, answer=answer,
                              correct_answer=correct_answer, score=score,
                              feedback=feedback, date=datetime.now())

            session.add(eval)
            logger.info(f"Evaluation saved: {eval}")
            session.commit()
            return "Evaluation saved"

        except Exception as e:
            return f"Error saving evaluation: {e}"


@app.post("/eval-service")
def evaluation(request: EvaluationRequest,
               current_user: Annotated[User, Depends(get_current_active_user)]
               ):
    try:
        if request.quizz_questions:
            feedback = []
            question_list = request.quizz_questions
            logger.info(f"question_list: {question_list}")
            answer_list = request.student_answers
            logger.info(f"answer_list: {answer_list}")

            for question, answer in zip(question_list, answer_list):
                correct_answer = json.loads(eval_answer(
                    question, answer
                ).content)
                logger.info(f"correct_answer: {correct_answer}")
                # request.student_responses.append(request.student_response)
                store_evals(
                    question, answer, correct_answer["correct_answer"],
                    correct_answer["score"], correct_answer["feedback"],
                    current_user
                    )

                feedback.append({
                            "question": question,
                            "student_answer": answer,
                            "correct_answer": correct_answer["correct_answer"],
                            "feedback": correct_answer["feedback"],
                            "score": correct_answer["score"],
                        })

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
            detail=f"Evaluation failed: {str(e)}"
        )


@app.post("/eval-service/evaluate_answer")
def evaluate_answer(request: SingleEvaluationRequest):
    try:
        response = eval_answer(request.question, request.answer)
        logger.info(f"Question answered: {response}")
        return json.loads(response.content)

    except Exception as e:
        logger.error(f"Evaluation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {str(e)}"
        )


@app.get("/eval-service/get-feedback")
def get_feedback(current_user:
                 Annotated[User, Depends(get_current_active_user)]
                 ):

    matching_keys = []
    cursor = '0'  # Start with cursor 0

    # Scan until the cursor returned by Redis is 0
    while cursor != 0:
        cursor, keys = redis_client.scan(
            cursor=cursor, match=f"Eval:{current_user.username}:*", count=100
            )
        logger.info(f"Matching keys: {matching_keys}")
        matching_keys.extend(keys)

    # Retrieve all the values for the found keys
    if matching_keys:
        values = redis_client.mget(matching_keys)
        logger.info(f"Values: {values}")
        return values
    else:
        return "No keys found for the pattern."


# Protected endpoint to test authentication
@app.get("/eval-service/me")
async def get_my_info(
    current_user: Annotated[User, Depends(get_current_active_user)]
        ):

    """Get current user info (for testing auth integration)"""
    return {
        "message": f"Hello {current_user.username}!",
        "user_info": current_user
    }
