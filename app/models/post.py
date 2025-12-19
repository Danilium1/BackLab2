from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy import String, Text

from .base import Base


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    descr: Mapped[str] = mapped_column(Text())

    def __repr__(self):
        return f"Post(id={self.id}, title={self.title})"
