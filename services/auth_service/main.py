from contextlib import asynccontextmanager
from datetime import timedelta
from typing import Annotated

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.auth_service.auth_utils import (
        ACCESS_TOKEN_EXPIRE_MINUTES,
        authenticate_user,
        create_access_token,
        get_current_active_user,
        get_user,
    )
    from services.auth_service.data_models import SignupUser, Token, User
    from services.auth_service.user_db import add_user, create_db_and_tables
else:
    from .auth_utils import (
        ACCESS_TOKEN_EXPIRE_MINUTES,
        authenticate_user,
        create_access_token,
        get_current_active_user,
        get_user,
    )
    from .data_models import SignupUser, Token, User
    from .user_db import add_user, create_db_and_tables

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from .logging_config import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Creating tables..")
    create_db_and_tables()
    logger.info("Tables created. Service is ready.")
    yield


app = FastAPI(title="Authentication Service", lifespan=lifespan)


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
    logger.info(f"User authenticated: {user.username}")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@app.get("/users/me/", response_model=User)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return {
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "disabled": current_user.disabled,
    }


@app.get("/users/me/items/")
async def read_own_items(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return [{"item_id": "Foo", "owner": current_user.username}]


@app.post("/signup", response_model=User)
async def signup_user(user: SignupUser):
    db_user = get_user(user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    try:
        new_user = add_user(
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            password=user.password,
        )
        logger.info(f"User created: {new_user.username}")
        # Manually create the response to match the User model
        # and avoid returning the hashed_password.
        return User(
            username=new_user.username,
            email=new_user.email,
            full_name=new_user.full_name,
            disabled=new_user.disabled,
        )
    except Exception as e:
        logger.error(f"Could not create user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not create user: {e}",
        )
