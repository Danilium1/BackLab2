from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.orm import mapped_column
from sqlalchemy import String

from .base import Base


class Allergen(Base):
    __tablename__ = "allergen"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)

    # Связь с рецептами через промежуточную таблицу
    recipe_allergens: Mapped[list["RecipeAllergen"]] = relationship(back_populates="allergen")

    def __repr__(self):
        return f"Allergen(id={self.id}, name={self.name})"
    
    
#deep file all