from datetime import datetime, timedelta, timezone
from typing import Annotated, TYPE_CHECKING, Any, Callable, cast
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from sqlmodel import Session, create_engine, select

# Import compatibility for both local pytest and container/module execution
if TYPE_CHECKING:
    from services.auth_service.auth_settings import auth_settings as auth_cfg
    from services.auth_service.data_models import User, UserInDB, User_Auth
    from services.auth_service.user_db import (
        update_user_password as _update_user_password,
    )
else:
    try:
        from services.auth_service.auth_settings import auth_settings as auth_cfg
        from services.auth_service.data_models import User, UserInDB, User_Auth
        from services.auth_service.user_db import (
            update_user_password as _update_user_password,
        )
    except Exception:
        from auth_settings import auth_settings as auth_cfg
        from data_models import User, UserInDB, User_Auth
        from user_db import update_user_password as _update_user_password


pwd_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

PG_PASSWORD = auth_cfg.PG_PASSWORD
DB_NAME = auth_cfg.DB_NAME
PORT = auth_cfg.DB_PORT
AUTH_SECRET = auth_cfg.SECRET_KEY
ALGORITHM = auth_cfg.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = 30

POSTGRES_URL = f"postgresql://postgres:{PG_PASSWORD}@postgres:{PORT}/{DB_NAME}"
engine = create_engine(POSTGRES_URL, echo=True)

# Evitar erro de mypy (attr-defined) com PyJWT, mantendo nomes estáveis
jwt_encode = cast("Callable[..., str]", getattr(jwt, "encode"))
jwt_decode = cast("Callable[..., Any]", getattr(jwt, "decode"))


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(username: str):
    with Session(engine) as session:
        statement = select(User_Auth).where(User_Auth.username == username)
        results = session.exec(statement)
        # user = results.first()
        # print(f"User: {user}")

        for row in results:
            if row.username is not None:
                user_dict = UserInDB(
                    username=row.username,
                    email=row.email,
                    full_name=row.full_name,
                    disabled=row.disabled,
                    hashed_password=row.hashed_password,
                )

                return user_dict


def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    # Rehash automático, se necessário (migração para bcrypt_sha256)
    try:
        if pwd_context.needs_update(user.hashed_password):
            new_hash = get_password_hash(password)
            try:
                _update_user_password(
                    username=user.username, new_hashed_password=new_hash
                )
                user.hashed_password = new_hash
            except Exception:
                pass
    except Exception:
        pass
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt_encode(to_encode, AUTH_SECRET, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt_decode(token, AUTH_SECRET, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception
    user = get_user(username=username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
