from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.orm import mapped_column
from sqlalchemy import String

from .base import Base


class Cuisine(Base):
    __tablename__ = "cuisine"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)

    # Связь с рецептами
    recipes: Mapped[list["Recipe"]] = relationship(back_populates="cuisine")

    def __repr__(self):
        return f"Cuisine(id={self.id}, name={self.name})"
    

#deep file all