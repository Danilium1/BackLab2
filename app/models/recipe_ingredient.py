from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.orm import mapped_column
from sqlalchemy import ForeignKey, Integer

from .base import Base


class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"

    id: Mapped[int] = mapped_column(primary_key=True)
    recipe_id: Mapped[int] = mapped_column(ForeignKey("recipes.id"))
    ingredient_id: Mapped[int] = mapped_column(ForeignKey("ingredient.id"))
    quantity: Mapped[int] = mapped_column(Integer)
    measurement: Mapped[int] = mapped_column(Integer)  # enum


    recipe: Mapped["Recipe"] = relationship(back_populates="recipe_ingredients")
    ingredient: Mapped["Ingredient"] = relationship(back_populates="recipe_ingredients")

    def __repr__(self):
        return f"RecipeIngredient(id={self.id}, recipe_id={self.recipe_id}, ingredient_id={self.ingredient_id})"
    
    
