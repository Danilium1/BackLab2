from fastapi import APIRouter

from config import settings

from .test import router as test_router
from .posts import router as posts_router
from .recipes import router as recipes_router
from .cuisines import router as cuisines_router
from .allergens import router as allergens_router
from .ingredients import router as ingredients_router

router = APIRouter(
    prefix=settings.url.prefix,
)
router.include_router(test_router)
router.include_router(posts_router)
router.include_router(recipes_router)
router.include_router(cuisines_router)
router.include_router(allergens_router)
router.include_router(ingredients_router)
