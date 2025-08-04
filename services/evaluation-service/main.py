from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from datetime import datetime, timedelta
from settings import settings
from sqlmodel import create_engine, Session, SQLModel
from utils.data_models import Evaluation, EvaluationRequest, User
from utils.auth_utils import get_current_active_user
from .model import eval_answer
import hashlib
import json
from infra.redis_cache import redis_client
from utils.data_models import Token
from utils.auth_utils import (
    authenticate_user, create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)


app = FastAPI(title="Evaluation Service")
PG_PASSWORD = settings.PG_PASSWORD
DB_NAME = settings.dbname
PORT = settings.port

postgres_url = (
    f"postgresql://postgres:{PG_PASSWORD}@localhost:{PORT}/{DB_NAME}"
    )

engine = create_engine(postgres_url, echo=True)
SQLModel.metadata.create_all(engine)


def store_evals(question: str, answer: str, feedback: str, username: str):

    with Session(engine) as session:
        try:
            eval = Evaluation(username=username.username,
                              question=question, answer=answer,
                              feedback=feedback, date=datetime.now())

            session.add(eval)
            session.commit()
            return "Evaluation saved"

        except Exception as e:
            return f"Error saving evaluation: {e}"


@app.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


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
                correct_answer = eval_answer(
                    question, answer
                ).content
                # request.student_responses.append(request.student_response)
                store_evals(
                    question, answer, correct_answer, current_user
                    )

                feedback.append({
                            "question": question,
                            "student_answer": answer,
                            "correct_answer": correct_answer,
                        })

            question_str = json.dumps(feedback, sort_keys=True)
            question_hash = hashlib.sha256(question_str.encode()).hexdigest()
            key = f"Eval:{current_user.username}:{question_hash}"
            redis_client.set(key, question_str)

            return {"request_id": question_hash, "feedback": feedback}

    except Exception as e:
        return e


@app.post("/eval-service/evaluate_answer")
def evaluate_answer(question: str, answer: str):
    try:
        response = eval_answer(question, answer)
        return response.content

    except Exception as e:
        return e


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
