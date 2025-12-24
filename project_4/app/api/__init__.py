from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer

from config import settings

from .test import router as test_router
from .posts import router as posts_router
from .categories import router as categories_router
from .tags import router as tags_router
from .users import router as users_router
from .auth import router as auth_router

http_bearer = HTTPBearer(auto_error=False)

router = APIRouter(
    prefix=settings.url.prefix,
    dependencies=[Depends(http_bearer)],
)
router.include_router(test_router)
router.include_router(posts_router)
router.include_router(categories_router)
router.include_router(tags_router)
router.include_router(users_router)
router.include_router(auth_router)
