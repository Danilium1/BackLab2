from typing import (
    TYPE_CHECKING,
    Annotated,
)
from fastapi_users.db import SQLAlchemyUserDatabase

from fastapi import Depends

from models import (
    db_helper,
    User,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


async def get_users_db(
    session: Annotated[
        "AsyncSession",
        Depends(db_helper.session_getter),
    ],
):
    yield SQLAlchemyUserDatabase(session, User)
