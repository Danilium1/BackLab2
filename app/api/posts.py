from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException
from models import db_helper, Post
from pydantic import BaseModel
from config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

router = APIRouter(
    tags=["Posts"],
    prefix=settings.url.posts,
)


class PostRead(BaseModel):
    id: int
    title: str
    descr: str


class PostCreate(BaseModel):
    title: str
    descr: str


@router.get("", response_model=list[PostRead])
async def index(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
):
    stmt = select(Post).order_by(Post.id)
    posts = await session.scalars(stmt)
    return posts.all()


@router.post("", response_model=PostRead, status_code=status.HTTP_201_CREATED)
async def store(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
    post_create: PostCreate,
):
    post = Post(title=post_create.title, descr=post_create.descr)
    session.add(post)
    await session.commit()
    return post


@router.get("/{id}", response_model=PostRead)
async def show(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
    id: int,
):
    post = await session.get(Post, id)
    return post


@router.put("/{id}", response_model=PostRead)
async def update(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
    id: int,
    post_update: PostCreate,
):
    post = await session.get(Post, id)
    post.title = post_update.title
    await session.commit()
    return post


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def destroy(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
    id: int,
):
    post = await session.get(Post, id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Post with id {id} not found"
        )

    await session.delete(post)
    await session.commit()
