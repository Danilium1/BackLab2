from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Integer, CheckConstraint, ForeignKey

from .base import Base


class Recipe(Base): # модель рецепта
    __tablename__ = "recipes"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    cooking_time: Mapped[int] = mapped_column(Integer)
    difficulty: Mapped[int] = mapped_column(Integer, default=1)
    cuisine_id: Mapped[int | None] = mapped_column(ForeignKey("cuisine.id"), nullable=True)

    # __table_args__ = (
    #     CheckConstraint(
    #         "difficulty >= 1 AND difficulty <= 5", name="check_difficulty_range"
    #     ),
    # )
    cuisine: Mapped["Cuisine"] = relationship(back_populates="recipes")
    recipe_ingredients: Mapped[list["RecipeIngredient"]] = relationship(back_populates="recipe")
    recipe_allergens: Mapped[list["RecipeAllergen"]] = relationship(back_populates="recipe")


    def __repr__(self):
        return f"Recipe(id={self.id}, title={self.title})"


