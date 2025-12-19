from typing import Annotated
from fastapi import APIRouter, Depends, status, HTTPException
from models import db_helper, Ingredient
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from config import settings

router = APIRouter(
    tags=["ingredients"],
    prefix=settings.url.ingredients,
)


# Pydantic схемы
class IngredientRead(BaseModel):
    id: int
    name: str
    
    class Config:
        from_attributes = True

class IngredientCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Название ингредиента")

class IngredientUpdate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Новое название ингредиента")

# CREATE - Создание ингредиента
@router.post("", response_model=IngredientRead, status_code=status.HTTP_201_CREATED, summary="Создать ингредиент")
async def create_ingredient(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
    ingredient_data: IngredientCreate,
):
    # Проверяем уникальность названия
    stmt = select(Ingredient).where(Ingredient.name == ingredient_data.name)
    existing_ingredient = await session.scalar(stmt)
    if existing_ingredient:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ingredient with name '{ingredient_data.name}' already exists"
        )
    
    # Создаем новый ингредиент
    ingredient = Ingredient(name=ingredient_data.name)
    session.add(ingredient)
    await session.commit()
    await session.refresh(ingredient)
    return ingredient

# READ ALL - Получение всех ингредиентов
@router.get("", response_model=list[IngredientRead], summary="Получить все ингредиенты")
async def get_ingredients(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
):
    stmt = select(Ingredient).order_by(Ingredient.id)
    ingredients = await session.scalars(stmt)
    return ingredients.all()

# READ ONE - Получение ингредиента по ID
@router.get("/{id}", response_model=IngredientRead, summary="Получить ингредиент по ID")
async def get_ingredient(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
    id: int,
):
    ingredient = await session.get(Ingredient, id)
    if not ingredient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ingredient with id {id} not found"
        )
    return ingredient

# UPDATE - Обновление ингредиента
@router.put("/{id}", response_model=IngredientRead, summary="Обновить ингредиент")
async def update_ingredient(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
    id: int,
    ingredient_update: IngredientUpdate,
):
    # Находим ингредиент
    ingredient = await session.get(Ingredient, id)
    if not ingredient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ingredient with id {id} not found"
        )
    
    # Проверяем уникальность нового названия
    stmt = select(Ingredient).where(
        Ingredient.name == ingredient_update.name,
        Ingredient.id != id  # исключаем текущий ингредиент из проверки
    )
    existing_ingredient = await session.scalar(stmt)
    if existing_ingredient:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ingredient with name '{ingredient_update.name}' already exists"
        )
    
    # Обновляем ингредиент
    ingredient.name = ingredient_update.name
    await session.commit()
    await session.refresh(ingredient)
    return ingredient

# DELETE - Удаление ингредиента
@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, summary="Удалить ингредиент")
async def delete_ingredient(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
    id: int,
):
    ingredient = await session.get(Ingredient, id)
    if not ingredient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ingredient with id {id} not found"
        )
    
    await session.delete(ingredient)
    await session.commit()