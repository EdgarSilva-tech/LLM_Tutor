from fastapi import FastAPI, Depends, HTTPException, status
from typing import Annotated
from datetime import datetime
from services.evaluation_service.eval_settings import eval_settings
from sqlmodel import create_engine, Session, SQLModel
from services.evaluation_service.data_models import (
    Evaluation, EvaluationRequest, User
    )
from services.evaluation_service.model import eval_answer
import hashlib
import json
from services.evaluation_service.cache import redis_client
from services.evaluation_service.auth_client import get_current_active_user


app = FastAPI(title="Evaluation Service")
PG_PASSWORD = eval_settings.PG_PASSWORD
DB_NAME = eval_settings.DB_NAME
PORT = eval_settings.DB_PORT

POSTGRES_URL = (
    f"postgresql://postgres:{PG_PASSWORD}@localhost:{PORT}/{DB_NAME}"
    )

engine = create_engine(POSTGRES_URL, echo=True)
SQLModel.metadata.create_all(engine)


def store_evals(question: str, answer: str, correct_answer: str,
                score: float, feedback: str, username: str):

    with Session(engine) as session:
        try:
            eval = Evaluation(username=username.username,
                              question=question, answer=answer,
                              correct_answer=correct_answer, score=score,
                              feedback=feedback, date=datetime.now())

            session.add(eval)
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
            answer_list = request.student_answers

            for question, answer in zip(question_list, answer_list):
                correct_answer = json.loads(eval_answer(
                    question, answer
                ).content)
                print(f"correct_answer: {correct_answer}")
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

            return {"request_id": question_hash, "feedback": feedback}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {str(e)}"
        )


@app.post("/eval-service/evaluate_answer")
def evaluate_answer(question: str, answer: str):
    try:
        response = eval_answer(question, answer)
        return json.loads(response.content)

    except Exception as e:
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
        matching_keys.extend(keys)

    # Retrieve all the values for the found keys
    if matching_keys:
        values = redis_client.mget(matching_keys)
        return values
    else:
        return "No keys found for the pattern."


# Health check endpoint
@app.get("/eval-service/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "evaluation-service"}


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
