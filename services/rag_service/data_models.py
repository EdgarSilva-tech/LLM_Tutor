from pydantic import BaseModel
from typing import List
from sqlmodel import Field, SQLModel
from uuid import UUID
import uuid
from typing import Any
from pgvector.sqlalchemy import Vector
from datetime import datetime


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


class Lesson_Embeddings(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    lesson_id: UUID = Field(foreign_key="khan_academy_lesson.id")
    chunk_index: int
    content: str
    embeddings: Any = Field(sa_type=Vector(1536))


class Khan_Academy_Lesson(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    content_path: str
    module: str
    topic: str
    date: datetime


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None
