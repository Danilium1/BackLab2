from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from models import db_helper, Category
from pydantic import BaseModel
from config import settings
from sqlalchemy import select

router = APIRouter(
    tags=["Categories"],
    prefix=settings.url.categories,
)


class CategoryRead(BaseModel):
    id: int
    name: str


class CategoryCreate(BaseModel):
    name: str


@router.get("", response_model=list[CategoryRead])
async def index(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
):
    stmt = select(Category).order_by(Category.id)
    categories = await session.scalars(stmt)
    return categories.all()


@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
async def store(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
    category_create: CategoryCreate,
):
    category = Category(name=category_create.name)
    session.add(category)
    await session.commit()
    return category
