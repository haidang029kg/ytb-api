from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class User(SQLModel, table=False):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(
        unique=True,
        index=True,
        description="Username",
    )
    email: str = Field(
        unique=True,
        index=True,
        description="Email",
    )

    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False
    created_at: datetime = Field(default_factory=datetime.now)


class UserInDb(User, table=True):
    password: str
