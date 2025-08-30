from pydantic import BaseModel


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
