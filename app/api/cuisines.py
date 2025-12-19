from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException
from models import db_helper, Cuisine
from pydantic import BaseModel, Field
from config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

router = APIRouter(
    tags=["cuisines"],
    prefix=settings.url.cuisines,  # Будет "/cuisines"
)

# Pydantic схема для чтения кухни
class CuisineRead(BaseModel):
    id: int
    name: str
    
    class Config:
        from_attributes = True

# Эндпоинт для получения всех кухонь
@router.get("", response_model=list[CuisineRead], summary="Получить все кухни")
async def get_cuisines(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
):
    stmt = select(Cuisine).order_by(Cuisine.id)
    cuisines = await session.scalars(stmt)
    return cuisines.all()

# Эндпоинт для получения одной кухни по ID
@router.get("/{id}", response_model=CuisineRead, summary="Получить кухню по ID")
async def get_cuisine(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
    id: int,
):
    cuisine = await session.get(Cuisine, id)
    if not cuisine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cuisine with id {id} not found"
        )
    return cuisine


# Схема для создания (без id)
class CuisineCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Название кухни")

# Эндпоинт для создания кухни
@router.post("", response_model=CuisineRead, status_code=status.HTTP_201_CREATED, summary="Создать кухню")
async def create_cuisine(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
    cuisine_data: CuisineCreate,
):
    # Проверяем уникальность названия
    stmt = select(Cuisine).where(Cuisine.name == cuisine_data.name)
    existing_cuisine = await session.scalar(stmt)
    if existing_cuisine:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cuisine with name '{cuisine_data.name}' already exists"
        )
    
    # Создаем новую кухню
    cuisine = Cuisine(name=cuisine_data.name)
    session.add(cuisine)
    await session.commit()
    await session.refresh(cuisine)
    return cuisine


# Схема для обновления кухни
class CuisineUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Новое название кухни")

# Эндпоинт для обновления кухни
@router.put("/{id}", response_model=CuisineRead, summary="Обновить кухню")
async def update_cuisine(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
    id: int,
    cuisine_update: CuisineUpdate,
):
    # Находим кухню
    cuisine = await session.get(Cuisine, id)
    if not cuisine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cuisine with id {id} not found"
        )
    
    # Проверяем уникальность нового названия
    stmt = select(Cuisine).where(
        Cuisine.name == cuisine_update.name,
        Cuisine.id != id  # исключаем текущую кухню из проверки
    )
    existing_cuisine = await session.scalar(stmt)
    if existing_cuisine:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cuisine with name '{cuisine_update.name}' already exists"
        )
    
    # Обновляем кухню
    cuisine.name = cuisine_update.name
    await session.commit()
    await session.refresh(cuisine)
    return cuisine

# Эндпоинт для удаления кухни
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, summary="Удалить кухню")
async def delete_cuisine(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
    id: int,
):
    cuisine = await session.get(Cuisine, id)
    if not cuisine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cuisine with id {id} not found"
        )
    
    await session.delete(cuisine)
    await session.commit()
