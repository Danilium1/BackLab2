from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException, Query
from sqlalchemy.orm import joinedload, selectinload, contains_eager
from models import db_helper, Post, Category, Tag, User
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from config import settings
from sqlalchemy import select
from authentication.fastapi_users import current_active_user

router = APIRouter(
    tags=["Posts"],
    prefix=settings.url.posts,
)


class TagRead(BaseModel):
    id: int
    name: str


class CategoryRead(BaseModel):
    id: int
    name: str


class PostCategoryRead(BaseModel):
    id: int
    title: str
    description: str
    category: CategoryRead
    tags: list[TagRead]


# class PostCategoryRead(BaseModel):
#     id: int
#     title: str
#     description: str
#     category: CategoryRead


class PostRead(BaseModel):
    id: int
    title: str
    description: str


class PostUpdate(BaseModel):
    title: str
    description: str


# class PostCreate(BaseModel):
#     title: str
#     description: str
#     category_id: int


class PostCreate(BaseModel):
    title: str
    description: str
    category_id: int
    tag_ids: list[int]


@router.get("", response_model=list[PostCategoryRead])
async def index(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
    user: User = Depends(current_active_user),
):
    stmt = select(Post).order_by(Post.id).options(selectinload(Post.tags))
    # stmt = select(Post).order_by(Post.id)
    # stmt = select(Post).order_by(Post.id).options(joinedload(Post.category))
    posts = await session.scalars(stmt)
    return posts.all()


@router.get("/example", response_model=list[PostCategoryRead])
async def example(
    search: Annotated[str, Query(max_length=50)],
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
):
    stmt = (
        select(Post)
        .outerjoin(Category)
        .where(Category.name == search)
        .options(contains_eager(Post.category))
        .order_by(Post.id)
    )

    # stmt = select(Post).join(Category).where(Category.name == search).order_by(Post.id)

    posts = await session.scalars(stmt)
    return posts.all()


@router.post("", response_model=PostCategoryRead, status_code=status.HTTP_201_CREATED)
async def store(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
    post_create: PostCreate,
):
    category = await session.get(Category, post_create.category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {post_create.category_id} not found",
        )

    tags = await session.scalars(select(Tag).where(Tag.id.in_(post_create.tag_ids)))

    post = Post(
        title=post_create.title,
        description=post_create.description,
        category=category,
        tags=tags.all(),
    )
    session.add(post)
    await session.commit()
    return post


@router.get("/{id}", response_model=PostCategoryRead)
async def show(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
    id: int,
):
    post = await session.get(Post, id, options=[selectinload(Post.tags)])
    return post


@router.put("/{id}", response_model=PostRead)
async def update(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
    id: int,
    post_update: PostUpdate,
):
    post = await session.get(Post, id)
    post.title = post_update.title
    post.description = post_update.description
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
