from fastapi import FastAPI, Depends, HTTPException, status
from typing import Annotated
from cache import redis_client
from model import quizz_generator
from data_models import QuizzRequest, User
import hashlib
import json
from auth_client import get_current_active_user

app = FastAPI(title="Quiz Generation Service")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Quiz Generation Service"}

@app.post("/generate-quiz")
def generate_quizz(request: QuizzRequest,
                   current_user:
                   Annotated[User, Depends(get_current_active_user)]
                   ):

    try:
        quizz = quizz_generator(
            request.topic, request.num_questions,
            request.difficulty, request.style
        )

        quizz_str = json.dumps({"questions": [quizz.content]}, sort_keys=True)
        quizz_hash = hashlib.sha256(quizz_str.encode()).hexdigest()
        cache_key = f"quizz_request:{current_user.username}:{quizz_hash}"
        redis_client.set(cache_key, quizz.content)

        return {"quizz_questions": quizz.content}

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Quizz generation failed: {str(e)}"
        )


@app.get("/get-quizz-questions")
def get_questions(current_user:
                  Annotated[User, Depends(get_current_active_user)]
                  ):
    try:
        matching_keys = []
        cursor = '0'  # Start with cursor 0

        # Scan until the cursor returned by Redis is 0
        while cursor != 0:
            cursor, keys = redis_client.scan(
                cursor=cursor,
                match=f"quizz_request:{current_user.username}:*",
                count=100
                )
            matching_keys.extend(keys)

        # Retrieve all the values for the found keys
        if matching_keys:
            values = redis_client.mget(matching_keys)
            return values
        else:
            return "No keys found for the pattern."

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get quizz questions: {str(e)}"
        )
