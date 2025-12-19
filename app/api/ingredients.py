from typing import Annotated, Optional
from fastapi import APIRouter, Depends, status, HTTPException, Query
from models import db_helper, Ingredient, Recipe, RecipeIngredient, RecipeAllergen
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from config import settings

# Import the format function from recipes to avoid duplication
from .recipes import format_recipe_response, RecipesRead

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


# GET /ingredients/{id}/recipes - получить все рецепты с данным ингредиентом
@router.get("/{id}/recipes", summary="Получить все рецепты с данным ингредиентом")
async def get_recipes_by_ingredient(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
    id: int,
    include: Optional[str] = Query(None, description="Include related data (comma-separated: cuisine, ingredients, allergens)"),
    select: Optional[str] = Query(None, description="Select specific fields (comma-separated: id, name, difficulty, description, cooking_time)"),
):
    # Проверяем существование ингредиента
    ingredient = await session.get(Ingredient, id)
    if not ingredient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ingredient with id {id} not found"
        )
    
    # Получаем все recipe_id, где используется этот ингредиент
    stmt = select(RecipeIngredient.recipe_id).where(RecipeIngredient.ingredient_id == id)
    result = await session.execute(stmt)
    recipe_ids = result.scalars().all()
    
    if not recipe_ids:
        return []
    
    # Parse include parameter
    includes = set()
    if include:
        includes = set(inc.strip() for inc in include.split(',') if inc.strip())
    
    # Build query with conditional eager loading based on include parameter
    stmt = select(Recipe).where(Recipe.id.in_(recipe_ids)).order_by(Recipe.id)
    
    # Only load relations if they are in the include list
    if 'cuisine' in includes:
        stmt = stmt.options(selectinload(Recipe.cuisine))
    if 'ingredients' in includes:
        stmt = stmt.options(
            selectinload(Recipe.recipe_ingredients).selectinload(RecipeIngredient.ingredient)
        )
    if 'allergens' in includes:
        stmt = stmt.options(
            selectinload(Recipe.recipe_allergens).selectinload(RecipeAllergen.allergen)
        )
    
    result = await session.execute(stmt)
    recipes = result.scalars().all()
    
    # Parse select parameter
    selected_fields = None
    if select:
        selected_fields = set(field.strip() for field in select.split(',') if field.strip())
        # Validate that selected fields are valid
        valid_fields = {'id', 'name', 'difficulty', 'description', 'cooking_time'}
        invalid_fields = selected_fields - valid_fields
        if invalid_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid fields in select: {', '.join(invalid_fields)}"
            )
    
    # Format response based on include and select parameters
    formatted_recipes = []
    for recipe in recipes:
        # Build response dict based on what was requested
        if selected_fields:
            # Only include selected fields from the Recipe entity
            recipe_dict = {}
            if 'id' in selected_fields:
                recipe_dict['id'] = recipe.id
            # Note: 'name' should map to 'title' in the Recipe model
            if 'name' in selected_fields:
                recipe_dict['name'] = recipe.title
            if 'difficulty' in selected_fields:
                recipe_dict['difficulty'] = recipe.difficulty
            if 'description' in selected_fields:
                recipe_dict['description'] = recipe.description
            if 'cooking_time' in selected_fields:
                recipe_dict['cooking_time'] = recipe.cooking_time
            formatted_recipes.append(recipe_dict)
        else:
            # Return all basic fields plus any included relations
            recipe_dict = {
                'id': recipe.id,
                'name': recipe.title,  # Map title to name as per spec
                'difficulty': recipe.difficulty,
                'description': recipe.description,
                'cooking_time': recipe.cooking_time
            }
            
            # Add included relations
            if 'cuisine' in includes:
                recipe_dict['cuisine'] = {
                    'id': recipe.cuisine.id,
                    'name': recipe.cuisine.name
                } if recipe.cuisine else None
            
            if 'ingredients' in includes:
                recipe_dict['ingredients'] = [
                    {
                        'id': ri.ingredient.id,
                        'name': ri.ingredient.name,
                        'quantity': ri.quantity,
                        'measurement': ri.measurement
                    }
                    for ri in recipe.recipe_ingredients
                ]
            
            if 'allergens' in includes:
                recipe_dict['allergens'] = [
                    {'id': ra.allergen.id, 'name': ra.allergen.name}
                    for ra in recipe.recipe_allergens
                ]
            
            formatted_recipes.append(recipe_dict)
    
    return formatted_recipes
