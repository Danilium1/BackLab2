from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException
from models import db_helper, Allergen
from pydantic import BaseModel, Field
from config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

router = APIRouter(
    tags=["allergens"],
    prefix=settings.url.allergens, )

# Pydantic схемы
class AllergenRead(BaseModel):
    id: int
    name: str
    
    class Config:
        from_attributes = True

class AllergenCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Название аллергена")

class AllergenUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Новое название аллергена")

# CREATE - Создание аллергена
@router.post("", response_model=AllergenRead, status_code=status.HTTP_201_CREATED, summary="Создать аллерген")
async def create_allergen(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
    allergen_data: AllergenCreate,
):
    # Проверяем уникальность названия
    stmt = select(Allergen).where(Allergen.name == allergen_data.name)
    existing_allergen = await session.scalar(stmt)
    if existing_allergen:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Allergen with name '{allergen_data.name}' already exists"
        )
    
    # Создаем новый аллерген
    allergen = Allergen(name=allergen_data.name)
    session.add(allergen)
    await session.commit()
    await session.refresh(allergen)
    return allergen

# READ ALL - Получение всех аллергенов
@router.get("", response_model=list[AllergenRead], summary="Получить все аллергены")
async def get_allergens(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
):
    stmt = select(Allergen).order_by(Allergen.id)
    allergens = await session.scalars(stmt)
    return allergens.all()

# READ ONE - Получение аллергена по ID
@router.get("/{id}", response_model=AllergenRead, summary="Получить аллерген по ID")
async def get_allergen(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
    id: int,
):
    allergen = await session.get(Allergen, id)
    if not allergen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Allergen with id {id} not found"
        )
    return allergen

# UPDATE - Обновление аллергена
@router.put("/{id}", response_model=AllergenRead, summary="Обновить аллерген")
async def update_allergen(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
    id: int,
    allergen_update: AllergenUpdate,
):
    # Находим аллерген
    allergen = await session.get(Allergen, id)
    if not allergen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Allergen with id {id} not found"
        )
    
    # Проверяем уникальность нового названия
    stmt = select(Allergen).where(
        Allergen.name == allergen_update.name,
        Allergen.id != id  # исключаем текущий аллерген из проверки
    )
    existing_allergen = await session.scalar(stmt)
    if existing_allergen:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Allergen with name '{allergen_update.name}' already exists"
        )
    
    # Обновляем аллерген
    allergen.name = allergen_update.name
    await session.commit()
    await session.refresh(allergen)
    return allergen

# DELETE - Удаление аллергена
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, summary="Удалить аллерген")
async def delete_allergen(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
    id: int,
):
    allergen = await session.get(Allergen, id)
    if not allergen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Allergen with id {id} not found"
        )
    
    await session.delete(allergen)
    await session.commit()