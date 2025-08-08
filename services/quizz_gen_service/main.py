from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from services.quizz_gen_service.cache import redis_client
from services.quizz_gen_service.model import quizz_generator
from services.quizz_gen_service.data_models import QuizzRequest, Token, User
from utils.auth_utils import (
    authenticate_user, create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES, get_current_active_user
)
from datetime import timedelta
import hashlib
import json

app = FastAPI()


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


@app.post("/generate-quizz")
def generate_quizz(request: QuizzRequest,
                   current_user:
                   Annotated[User, Depends(get_current_active_user)]
                   ):

    quizz = quizz_generator(
        request.topic, request.num_questions,
        request.difficulty, request.style
    )

    quizz_str = json.dumps({"questions": [quizz.content]}, sort_keys=True)
    quizz_hash = hashlib.sha256(quizz_str.encode()).hexdigest()
    cache_key = f"quizz_request:{current_user.username}:{quizz_hash}"
    redis_client.set(cache_key, quizz.content)

    return {"quizz_questions": quizz.content}


@app.get("/get-quizz-questions")
def get_questions(current_user:
                  Annotated[User, Depends(get_current_active_user)]
                  ):
    matching_keys = []
    cursor = '0'  # Start with cursor 0

    # Scan until the cursor returned by Redis is 0
    while cursor != 0:
        cursor, keys = redis_client.scan(
            cursor=cursor, match=f"quizz_request:{current_user.username}:*",
            count=100
            )
        matching_keys.extend(keys)

    # Retrieve all the values for the found keys
    if matching_keys:
        values = redis_client.mget(matching_keys)
        return values
    else:
        return "No keys found for the pattern."
