from fastapi import FastAPI
from pydantic import BaseModel
from infra.redis_cache import redis_client

app = FastAPI()

class QuizzRequest(BaseModel):
    topic: str
    num_questions: int
    difficulty: str
    style: str


@app.post("/generate-quizz")
def generate_quizz(request: QuizzRequest):
    quizz = generate_quizz(
        request.topic, request.num_questions,
        request.difficulty, request.style
    )

    cache_key = f"quizz_request_{request.topic}:{request.num_questions}:{request.difficulty}:{request.style}"
    redis_client.set(cache_key, [quizz.content])

    return {"quizz_questions": [quizz.content]}


@app.get("/get-quizz-questions")
def get_questions(request: QuizzRequest):
    cache_key = f"quizz_request_{request.topic}:{request.num_questions}:{request.difficulty}:{request.style}"
    questions = redis_client.get(cache_key)

    return questions
