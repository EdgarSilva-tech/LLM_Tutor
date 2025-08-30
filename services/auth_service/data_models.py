from pydantic import BaseModel
from sqlmodel import Field, SQLModel
import uuid
from uuid import UUID


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


class SignupUser(BaseModel):
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
