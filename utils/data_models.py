from pydantic import BaseModel
from uuid import UUID
import uuid
from sqlmodel import Field, SQLModel
from typing import List


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None


class UserInDB(User):
    hashed_password: str


class SignupUser:
    username: str
    email: str
    full_name: str
    password: str


class User_Auth(SQLModel, table=True):
    user_id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None
    hashed_password: str


# class EvaluationRequest(BaseModel):
#     student_id: str
#     quizz_questions: List[str]
#     student_answers: List[str]


# class Evaluation(SQLModel, table=True):
#     eval_id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
#     username: str = Field(index=True)
#     question: str
#     answer: str
#     feedback: str
#     date: datetime


class QueryRequest(BaseModel):
    question: str
    top_k: int = 5


class QueryResponse(BaseModel):
    answer: str
    context: List[str]
    sources: List[str]


class EmbeddingRequest(BaseModel):
    text: str


class EmbeddingResponse(BaseModel):
    embedding: List[float]


class QuizzRequest(BaseModel):
    topic: str
    num_questions: int
    difficulty: str
    style: str
