from typing import Annotated
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from models import db_helper, Tag
from pydantic import BaseModel
from config import settings
from sqlalchemy import select

router = APIRouter(
    tags=["Tags"],
    prefix=settings.url.tags,
)


class TagRead(BaseModel):
    id: int
    name: str


class TagCreate(BaseModel):
    name: str


@router.get("", response_model=list[TagRead])
async def index(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
):
    stmt = select(Tag).order_by(Tag.id)
    tags = await session.scalars(stmt)
    return tags.all()


@router.post("", response_model=TagRead, status_code=status.HTTP_201_CREATED)
async def store(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
    tag_create: TagCreate,
):
    tag = Tag(name=tag_create.name)
    session.add(tag)
    await session.commit()
    return tag
