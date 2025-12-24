from fastapi import APIRouter

from authentication.fastapi_users import fastapi_users
from config import settings
from authentication.schemas.user import (
    UserRead,
    UserUpdate,
)

router = APIRouter(
    prefix=settings.url.users,
    tags=["Users"],
)

# /me
# /{id}
router.include_router(
    router=fastapi_users.get_users_router(
        UserRead,
        UserUpdate,
    ),
)
