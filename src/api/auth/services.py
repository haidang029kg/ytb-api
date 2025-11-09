from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.settings import settings
from src.db import get_async_session
from src.models.users import User, UserInDb

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

http_bearer_security = HTTPBearer()


async def get_authenticated_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(http_bearer_security)],
    db_session: Annotated[AsyncSession, Depends(get_async_session)],
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    access_token = credentials.credentials
    try:
        payload = decode_token(access_token)
    except jwt.InvalidTokenError:
        raise credentials_exception

    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception

    iat: int = payload.get("iat")
    iat_time = datetime.fromtimestamp(iat, tz=timezone.utc)

    if iat_time + timedelta(days=settings.ACCESS_TOKEN_MAX_LIFE_TIME_DAYS) < datetime.now(
        tz=timezone.utc
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token (max lifetime)"
        )

    user = await db_session.exec(select(UserInDb).where(UserInDb.username == username))
    user = user.first()

    if user is None:
        raise credentials_exception

    return user


def validate_refresh_token(user: User, refresh_token: str):
    try:
        data = decode_token(refresh_token)
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid refresh token!"
        )
    username: str = data.get("sub")
    if username is None or username != user.username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid refresh token!"
        )

    return data


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    expire = datetime.now(tz=timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str):
    return jwt.decode(token, settings.SECRET_KEY, algorithms=settings.ALGORITHM)


def hash_password(plaintext_pass: str):
    return pwd_context.hash(plaintext_pass)


def verify_password(plaintext_pass: str, hashed_password: str):
    return pwd_context.verify(plaintext_pass, hashed_password)


async def create_confirm_token(user_id: str):
    payload = dict(user_id=user_id)
    token = create_access_token(payload, timedelta(days=7))
    return token


async def create_an_example(user_id: str):
    print()
