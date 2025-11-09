from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.core.settings import settings
from src.db import get_async_session
from src.models.users import User, UserInDb
from src.schemas.users import LoginReq, RefreshTokenReq, Token, TokenRenew, UserCreateReq
from src.services import user_ser, user_signal_ser
from src.services.authentication import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_authenticated_user,
    hash_password,
    validate_refresh_token,
    verify_password,
)
from src.core.logger import logger

auth_routes = APIRouter(prefix="/auth")


@auth_routes.post("/registration")
async def register(
    data: UserCreateReq,
    session: Annotated[AsyncSession, Depends(get_async_session)],
    background_tasks: BackgroundTasks,
) -> User:
    if data.password != data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="password confirm does not match",
        )

    user = UserInDb(
        email=data.email,
        username=data.username,
        password=hash_password(data.password),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    user_hook = user_signal_ser.UserSignalHandler()
    background_tasks.add_task(
        user_hook.run, event=user_signal_ser.UserSignalEventType.ON_REGISTRATION, user_id=user.id
    )

    return user


@auth_routes.post("/registration/confirmation/resend")
async def send_on_registration(
    user: Annotated[User, Depends(get_authenticated_user)],
    background_tasks: BackgroundTasks,
) -> dict:
    user_hook = user_signal_ser.UserSignalHandler()
    background_tasks.add_task(
        user_hook.run, event=user_signal_ser.UserSignalEventType.ON_REGISTRATION, user_id=user.id
    )

    return dict(message="Email verification has been sent to your mailbox", status="OK")


@auth_routes.get("/registration/confirmation")
async def confirm_registration(
    token: Annotated[str, Query()],
    db_session: Annotated[AsyncSession, Depends(get_async_session)],
    background_tasks: BackgroundTasks,
) -> User:
    if not token:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="")

    data = decode_token(token)
    user_id = data.get("user_id")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="")

    user = await user_ser.get_user(user_id=user_id, db_session=db_session)

    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="")

    if user.is_verified is True:
        return user

    user.is_verified = True

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    user_hook = user_signal_ser.UserSignalHandler()
    background_tasks.add_task(
        user_hook.run,
        event=user_signal_ser.UserSignalEventType.ON_COMPLETE_REGISTRATION,
        user_id=user.id,
    )

    return user


@auth_routes.post("/token")
async def login(
    data: LoginReq,
    db_session: Annotated[AsyncSession, Depends(get_async_session)],
) -> Token:
    logger.info("Begin request")
    logger.info("Begin request")
    logger.info("Begin request")
    logger.info("Begin request")
    logger.info("Begin request")
    logger.info("Begin request")
    logger.info("Begin request")
    logger.info("Begin request")
    logger.info("Begin request")
    user = await db_session.exec(select(UserInDb).where(UserInDb.username == data.username))
    user = user.first()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User does not exist!")

    if verify_password(data.password, user.password) is False:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Incorrect username or password")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": user.username, "iat": datetime.now(tz=timezone.utc)}

    access_token = create_access_token(data=payload, expires_delta=access_token_expires)
    refresh_token = create_refresh_token(data=payload)
    return Token(access_token=access_token, refresh_token=refresh_token, token_type="Bearer")


@auth_routes.post("/token/refresh")
async def refresh_token(
    data: RefreshTokenReq,
    user: Annotated[User, Depends(get_authenticated_user)],
) -> TokenRenew:
    # verify refresh token
    payload = validate_refresh_token(user=user, refresh_token=data.refresh_token)
    return TokenRenew(access_token=create_access_token(payload), token_type="Bearer")


@auth_routes.get("/me")
async def get_current_user(
    user: Annotated[User, Depends(get_authenticated_user)],
) -> User:
    return user
