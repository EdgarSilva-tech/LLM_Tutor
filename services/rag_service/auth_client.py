# services/rag_service/auth_client.py
import httpx
import asyncio
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from data_models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user_from_auth_service(token: str) -> User:
    headers = {"Authorization": f"Bearer {token}"}
    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    "http://auth-service:8001/users/me/",
                    headers=headers,
                )
                if response.status_code == 200:
                    user_data = response.json()
                    return User(**user_data)
                elif response.status_code == 401:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Could not validate credentials",
                        headers={"WWW-Authenticate": "Bearer"},
                    )
                else:
                    if attempt < 2:
                        await asyncio.sleep(0.2 * (2**attempt))
                        continue
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Auth service error",
                    )
        except httpx.RequestError:
            if attempt < 2:
                await asyncio.sleep(0.2 * (2**attempt))
                continue
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Auth service unavailable",
            )


async def get_current_active_user(token: str = Depends(oauth2_scheme)) -> User:
    return await get_current_user_from_auth_service(token)
