from typing import Annotated

from src.db import get_async_session
from fastapi import Depends
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.models import users as user_model


async def get_user(
    user_id: str | int,
    db_session: Annotated[AsyncSession, Depends(get_async_session)],
) -> user_model.User | None:
    user = await db_session.exec(
        select(user_model.UserInDb).where(user_model.UserInDb.id == user_id)
    )
    user = user.first()
    return user
