from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.orm import mapped_column
from sqlalchemy import String

from .base import Base


class Ingredient(Base):
    __tablename__ = "ingredient"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)

    # Связь с рецептами через промежуточную таблицу
    recipe_ingredients: Mapped[list["RecipeIngredient"]] = relationship(back_populates="ingredient")

    def __repr__(self):
        return f"Ingredient(id={self.id}, name={self.name})"


#deep file all