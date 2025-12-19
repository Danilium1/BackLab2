from typing import Annotated, Optional
from fastapi import APIRouter, Depends, status, HTTPException, Query
from models import db_helper, Recipe, Cuisine, Allergen, Ingredient, RecipeAllergen, RecipeIngredient, MeasurementEnum
from pydantic import BaseModel, Field
from config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from sqlalchemy.orm import selectinload
from fastapi_filter import FilterDepends, with_prefix
from fastapi_filter.contrib.sqlalchemy import Filter
from fastapi_pagination import Page, add_pagination, Params
from fastapi_pagination.ext.sqlalchemy import paginate as apaginate

router = APIRouter(
    tags=["recipes"],
    prefix=settings.url.recipes,
)

# Filter class for Recipe
class RecipeFilter(Filter):
    name__like: Optional[str] = None
    ingredient_id: Optional[str] = None  # Comma-separated list of ingredient IDs
    order_by: list[str] = ["-id"]  # Default sorting by id descending

    class Constants(Filter.Constants):
        model = Recipe
        search_field_name = "name"
        search_model_fields = ["title"]

# Схемы для создания
class RecipeIngredientCreate(BaseModel):
    ingredient_id: int
    quantity: int = Field(..., gt=0, description="Количество ингредиента")
    measurement: int = Field(..., description="Единица измерения (1=г, 2=шт, 3=мл)")

class RecipesCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Название рецепта")
    description: str = Field(..., min_length=1, description="Описание рецепта")
    cooking_time: int = Field(..., gt=0, description="Время готовки в минутах")
    difficulty: int = Field(default=1, ge=1, le=5, description="Сложность блюда от 1 до 5")
    cuisine_id: int | None = Field(None, description="ID кухни")
    allergen_ids: list[int] = Field(default=[], description="Список ID аллергенов")
    ingredients: list[RecipeIngredientCreate] = Field(..., description="Список ингредиентов")

# Схемы для чтения
class CuisineInfo(BaseModel):
    id: int
    name: str
    
    class Config:
        from_attributes = True

class AllergenInfo(BaseModel):
    id: int
    name: str
    
    class Config:
        from_attributes = True

class IngredientInfo(BaseModel):
    id: int
    name: str
    quantity: int
    measurement: int
    
    class Config:
        from_attributes = True

class RecipesRead(BaseModel):
    id: int
    title: str
    description: str
    cooking_time: int
    difficulty: int
    cuisine: CuisineInfo | None
    allergens: list[AllergenInfo]
    ingredients: list[IngredientInfo]
    
    class Config:
        from_attributes = True

# Helper function to format recipe with relations
def format_recipe_response(recipe: Recipe) -> dict:
    """Format recipe with all relations into the required response format"""
    return {
        "id": recipe.id,
        "title": recipe.title,
        "description": recipe.description,
        "cooking_time": recipe.cooking_time,
        "difficulty": recipe.difficulty,
        "cuisine": {
            "id": recipe.cuisine.id,
            "name": recipe.cuisine.name
        } if recipe.cuisine else None,
        "allergens": [
            {"id": ra.allergen.id, "name": ra.allergen.name}
            for ra in recipe.recipe_allergens
        ],
        "ingredients": [
            {
                "id": ri.ingredient.id,
                "name": ri.ingredient.name,
                "quantity": ri.quantity,
                "measurement": ri.measurement
            }
            for ri in recipe.recipe_ingredients
        ]
    }

@router.get("", summary="читаем все рецепты")
async def index(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
    params: Params = Depends(),
    name__like: Optional[str] = Query(None, description="Search recipes by name (partial match)"),
    ingredient_id: Optional[str] = Query(None, description="Filter by ingredient IDs (comma-separated)"),
    sort: str = Query("-id", description="Sort by field (e.g., 'id', '-id', 'difficulty', '-difficulty')"),
):
    # Build base query with eager loading of relationships
    stmt = (
        select(Recipe)
        .options(
            selectinload(Recipe.cuisine),
            selectinload(Recipe.recipe_allergens).selectinload(RecipeAllergen.allergen),
            selectinload(Recipe.recipe_ingredients).selectinload(RecipeIngredient.ingredient)
        )
    )
    
    # Apply name filter (case-insensitive partial match)
    if name__like:
        stmt = stmt.where(Recipe.title.ilike(f"%{name__like}%"))
    
    # Apply ingredient filter
    if ingredient_id:
        ingredient_ids = [int(id.strip()) for id in ingredient_id.split(',') if id.strip()]
        if ingredient_ids:
            # Filter recipes that contain at least one of the specified ingredients
            stmt = stmt.join(Recipe.recipe_ingredients).where(
                RecipeIngredient.ingredient_id.in_(ingredient_ids)
            ).distinct()
    
    # Apply sorting
    if sort:
        if sort.startswith('-'):
            # Descending order
            field = sort[1:]
            if field == 'id':
                stmt = stmt.order_by(Recipe.id.desc())
            elif field == 'difficulty':
                stmt = stmt.order_by(Recipe.difficulty.desc())
        else:
            # Ascending order
            if sort == 'id':
                stmt = stmt.order_by(Recipe.id.asc())
            elif sort == 'difficulty':
                stmt = stmt.order_by(Recipe.difficulty.asc())
    
    # Use pagination
    page = await apaginate(session, stmt, params=params)
    
    # Transform the page items to use format_recipe_response
    formatted_items = [format_recipe_response(recipe) for recipe in page.items]
    
    # Return a dict with pagination info
    return {
        'items': formatted_items,
        'total': page.total,
        'page': page.page,
        'size': page.size,
        'pages': page.pages
    }


@router.post("", response_model=RecipesRead, status_code=status.HTTP_201_CREATED, summary="делаем один рецепт")
async def store(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
    recipe_create: RecipesCreate,
):
    # 1. Проверяем существование кухни (если указана)
    if recipe_create.cuisine_id:
        cuisine = await session.get(Cuisine, recipe_create.cuisine_id)
        if not cuisine:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cuisine with id {recipe_create.cuisine_id} not found"
            )

    # 2. Проверяем существование аллергенов
    if recipe_create.allergen_ids:
        stmt = select(Allergen).where(Allergen.id.in_(recipe_create.allergen_ids))
        allergens = await session.scalars(stmt)
        existing_allergens = allergens.all()
        
        if len(existing_allergens) != len(recipe_create.allergen_ids):
            existing_ids = {a.id for a in existing_allergens}
            missing_ids = set(recipe_create.allergen_ids) - existing_ids
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Allergens with ids {missing_ids} not found"
            )

    # 3. Проверяем существование ингредиентов
    ingredient_ids = [ing.ingredient_id for ing in recipe_create.ingredients]
    stmt = select(Ingredient).where(Ingredient.id.in_(ingredient_ids))
    ingredients = await session.scalars(stmt)
    existing_ingredients = ingredients.all()
    
    if len(existing_ingredients) != len(ingredient_ids):
        existing_ing_ids = {i.id for i in existing_ingredients}
        missing_ing_ids = set(ingredient_ids) - existing_ing_ids
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ingredients with ids {missing_ing_ids} not found"
        )

    # 4. Создаем рецепт
    recipe = Recipe(
        title=recipe_create.title,
        description=recipe_create.description,
        cooking_time=recipe_create.cooking_time,
        difficulty=recipe_create.difficulty,
        cuisine_id=recipe_create.cuisine_id
    )
    session.add(recipe)
    await session.flush()  # Получаем ID рецепта

    # 5. Добавляем связи с аллергенами
    for allergen_id in recipe_create.allergen_ids:
        recipe_allergen = RecipeAllergen(
            recipe_id=recipe.id,
            allergen_id=allergen_id
        )
        session.add(recipe_allergen)

    # 6. Добавляем ингредиенты
    for ingredient_data in recipe_create.ingredients:
        recipe_ingredient = RecipeIngredient(
            recipe_id=recipe.id,
            ingredient_id=ingredient_data.ingredient_id,
            quantity=ingredient_data.quantity,
            measurement=ingredient_data.measurement
        )
        session.add(recipe_ingredient)

    # 7. Сохраняем все изменения
    await session.commit()

    # 8. Загружаем связанные данные для ответа (нужна новая транзакция)
    stmt = (
        select(Recipe)
        .where(Recipe.id == recipe.id)
        .options(
            selectinload(Recipe.cuisine),
            selectinload(Recipe.recipe_allergens).selectinload(RecipeAllergen.allergen),
            selectinload(Recipe.recipe_ingredients).selectinload(RecipeIngredient.ingredient)
        )
    )
    result = await session.execute(stmt)
    recipe_with_relations = result.scalar_one()

    return format_recipe_response(recipe_with_relations)


@router.get("/{id}", response_model=RecipesRead, summary="читаем один рецепт")
async def show(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
    id: int,
):
    stmt = (
        select(Recipe)
        .where(Recipe.id == id)
        .options(
            selectinload(Recipe.cuisine),
            selectinload(Recipe.recipe_allergens).selectinload(RecipeAllergen.allergen),
            selectinload(Recipe.recipe_ingredients).selectinload(RecipeIngredient.ingredient)
        )
    )
    result = await session.execute(stmt)
    recipe = result.scalar_one_or_none()
    
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipe with id {id} not found"
        )
    
    return format_recipe_response(recipe)

@router.put("/{id}", response_model=RecipesRead, summary="обновить один рецепт")
async def update(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
    id: int,
    recipe_update: RecipesCreate,
):
    # 1. Проверяем существование рецепта
    recipe = await session.get(Recipe, id)
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipe with id {id} not found"
        )
    
    # 2. Проверяем существование кухни (если указана)
    if recipe_update.cuisine_id:
        cuisine = await session.get(Cuisine, recipe_update.cuisine_id)
        if not cuisine:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cuisine with id {recipe_update.cuisine_id} not found"
            )

    # 3. Проверяем существование аллергенов
    if recipe_update.allergen_ids:
        stmt = select(Allergen).where(Allergen.id.in_(recipe_update.allergen_ids))
        allergens = await session.scalars(stmt)
        existing_allergens = allergens.all()
        
        if len(existing_allergens) != len(recipe_update.allergen_ids):
            existing_ids = {a.id for a in existing_allergens}
            missing_ids = set(recipe_update.allergen_ids) - existing_ids
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Allergens with ids {missing_ids} not found"
            )

    # 4. Проверяем существование ингредиентов
    ingredient_ids = [ing.ingredient_id for ing in recipe_update.ingredients]
    stmt = select(Ingredient).where(Ingredient.id.in_(ingredient_ids))
    ingredients = await session.scalars(stmt)
    existing_ingredients = ingredients.all()
    
    if len(existing_ingredients) != len(ingredient_ids):
        existing_ing_ids = {i.id for i in existing_ingredients}
        missing_ing_ids = set(ingredient_ids) - existing_ing_ids
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ingredients with ids {missing_ing_ids} not found"
        )
    
    # 5. Обновляем основные поля рецепта
    recipe.title = recipe_update.title
    recipe.description = recipe_update.description
    recipe.cooking_time = recipe_update.cooking_time
    recipe.difficulty = recipe_update.difficulty
    recipe.cuisine_id = recipe_update.cuisine_id
    
    # 6. Удаляем старые связи с аллергенами
    stmt = select(RecipeAllergen).where(RecipeAllergen.recipe_id == id)
    result = await session.execute(stmt)
    old_recipe_allergens = result.scalars().all()
    for ra in old_recipe_allergens:
        await session.delete(ra)
    
    # 7. Добавляем новые связи с аллергенами
    for allergen_id in recipe_update.allergen_ids:
        recipe_allergen = RecipeAllergen(
            recipe_id=recipe.id,
            allergen_id=allergen_id
        )
        session.add(recipe_allergen)
    
    # 8. Удаляем старые ингредиенты
    stmt = select(RecipeIngredient).where(RecipeIngredient.recipe_id == id)
    result = await session.execute(stmt)
    old_recipe_ingredients = result.scalars().all()
    for ri in old_recipe_ingredients:
        await session.delete(ri)
    
    # 9. Добавляем новые ингредиенты
    for ingredient_data in recipe_update.ingredients:
        recipe_ingredient = RecipeIngredient(
            recipe_id=recipe.id,
            ingredient_id=ingredient_data.ingredient_id,
            quantity=ingredient_data.quantity,
            measurement=ingredient_data.measurement
        )
        session.add(recipe_ingredient)
    
    # 10. Сохраняем изменения
    await session.commit()
    
    # 11. Загружаем обновленный рецепт со всеми связями
    stmt = (
        select(Recipe)
        .where(Recipe.id == id)
        .options(
            selectinload(Recipe.cuisine),
            selectinload(Recipe.recipe_allergens).selectinload(RecipeAllergen.allergen),
            selectinload(Recipe.recipe_ingredients).selectinload(RecipeIngredient.ingredient)
        )
    )
    result = await session.execute(stmt)
    recipe_with_relations = result.scalar_one()
    
    return format_recipe_response(recipe_with_relations)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, summary="удаление рецепта")
async def destroy(
    session: Annotated[
        AsyncSession,
        Depends(db_helper.session_getter),
    ],
    id: int,
):
    # 1. Проверяем существование рецепта
    recipe = await session.get(Recipe, id)
    if not recipe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Recipe with id {id} not found"
        )
    
    # 2. Удаляем связи с аллергенами
    stmt = select(RecipeAllergen).where(RecipeAllergen.recipe_id == id)
    result = await session.execute(stmt)
    recipe_allergens = result.scalars().all()
    for ra in recipe_allergens:
        await session.delete(ra)
    
    # 3. Удаляем связи с ингредиентами
    stmt = select(RecipeIngredient).where(RecipeIngredient.recipe_id == id)
    result = await session.execute(stmt)
    recipe_ingredients = result.scalars().all()
    for ri in recipe_ingredients:
        await session.delete(ri)
    
    # 4. Удаляем сам рецепт
    await session.delete(recipe)
    
    # 5. Сохраняем изменения
    await session.commit()


# @router.put("/{id}", response_model=RecipesRead, summary="обновить один рецепт")
# async def update(
#     session: Annotated[
#         AsyncSession,
#         Depends(db_helper.session_getter),
#     ],
#     id: int,
#     recipe_update: RecipesCreate,
# ):
#     recipe = await session.get(Recipe, id)
#     recipe.title = recipe_update.title
#     recipe.description = recipe_update.description
#     recipe.cooking_time = recipe_update.cooking_time
#     recipe.difficulty = recipe_update.difficulty
#     await session.commit()
#     return recipe


# @router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT, summary="удаление рецепта")
# async def destroy(
#     session: Annotated[
#         AsyncSession,
#         Depends(db_helper.session_getter),
#     ],
#     id: int,
# ):
#     recipe = await session.get(Recipe, id)
#     if not recipe:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND, detail=f"Recipe with id {id} not found"
#         )

#     await session.delete(recipe)
#     await session.commit()