from pydantic import BaseModel
from sqlmodel import Field, SQLModel, Column
import uuid
from uuid import UUID
from datetime import datetime
from sqlalchemy.dialects import postgresql
from sqlalchemy import String


class QuizzRequest(BaseModel):
    topic: str
    num_questions: int
    difficulty: str
    style: str


class Token(BaseModel):
    access_token: str
    token_type: str


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None


class SubmitAnswers(BaseModel):
    quizz_id: str
    answers: list[str]


class Quizz(SQLModel, table=True):
    quizz_id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    username: str = Field(index=True)
    topic: str
    num_questions: int
    difficulty: str
    style: str
    questions: list[str] = Field(sa_column=Column(postgresql.ARRAY(String())))
    tags: list[str] = Field(sa_column=Column(postgresql.ARRAY(String())))
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        arbitrary_types_allowed = True
