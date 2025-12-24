from typing import TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, ForeignKey, Table, Column

from .base import Base

if TYPE_CHECKING:
    from .users import User


association_table = Table(
    "association",
    Base.metadata,
    Column("post_id", ForeignKey("posts.id")),
    Column("tag_id", ForeignKey("tags.id")),
)


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, nullable=True)

    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"))
    category: Mapped["Category"] = relationship(back_populates="posts", lazy="joined")
    # category: Mapped["Category"] = relationship(back_populates="posts")

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="posts")

    tags: Mapped[list["Tag"]] = relationship(
        secondary=association_table, back_populates="posts"
    )

    def __repr__(self):
        return f"Post(id={self.id}, title={self.title})"


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    posts: Mapped[list["Post"]] = relationship(back_populates="category")

    def __repr__(self):
        return f"Category(id={self.id}, name={self.name})"


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))

    posts: Mapped[list["Post"]] = relationship(
        secondary=association_table, back_populates="tags"
    )

    def __repr__(self):
        return f"Tag(id={self.id}, name={self.name})"
