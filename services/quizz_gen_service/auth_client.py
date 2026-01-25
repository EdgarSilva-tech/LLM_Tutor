import time
import httpx
import asyncio
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from .data_models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Cache simples em memória (por processo) para reduzir chamadas ao auth-service sob carga
_TOKEN_CACHE_TTL_SECONDS = 30
_token_cache: dict[str, tuple[User, float]] = {}


def _get_cached_user(token: str) -> User | None:
    item = _token_cache.get(token)
    if not item:
        return None
    user, expires_at = item
    if expires_at < time.time():
        _token_cache.pop(token, None)
        return None
    return user


def _set_cached_user(token: str, user: User) -> None:
    _token_cache[token] = (user, time.time() + _TOKEN_CACHE_TTL_SECONDS)


async def get_current_user_from_auth_service(token: str) -> User:
    # tenta cache primeiro
    cached = _get_cached_user(token)
    if cached:
        return cached
    headers = {"Authorization": f"Bearer {token}"}
    # retry simples com backoff exponencial
    for attempt in range(3):
        try:
            timeout = httpx.Timeout(5.0, connect=3.0, read=5.0)
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(
                    "http://auth-service:8001/users/me/", headers=headers
                )
                if response.status_code == 200:
                    user_data = response.json()
                    user = User(**user_data)
                    _set_cached_user(token, user)
                    return user
                elif response.status_code == 401:
                    # token inválido: invalida cache e falha
                    _token_cache.pop(token, None)
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Could not validate credentials",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                else:
                    # respostas 5xx/4xx diferentes de 401: tente novamente
                    if attempt < 2:
                        await asyncio.sleep(0.2 * (2**attempt))
                        continue
                    # último recurso: se houver cache válido, usa
                    if cached:
                        return cached
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="Auth service error",
                    )
        except httpx.RequestError:
            if attempt < 2:
                await asyncio.sleep(0.2 * (2**attempt))
                continue
            # timeout/erro de rede: fallback para cache, se existir
            if cached:
                return cached
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Auth service unavailable",
            )

    if cached is not None:
        return cached
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Auth service unavailable",
    )


async def get_current_active_user(token: str = Depends(oauth2_scheme)) -> User:
    return await get_current_user_from_auth_service(token)
