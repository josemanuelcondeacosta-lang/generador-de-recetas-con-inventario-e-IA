from datetime import datetime

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "usuarios"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))


class Ingredient(Base):
    __tablename__ = "ingredientes"
    __table_args__ = (
        UniqueConstraint("user_id", "normalized_name"),
        CheckConstraint("quantity > 0"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(80))
    normalized_name: Mapped[str] = mapped_column(String(240))
    quantity: Mapped[float]
    unit: Mapped[str] = mapped_column(String(30))


class Recipe(Base):
    __tablename__ = "recetas"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"), index=True)
    content: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    rating: Mapped["Rating | None"] = relationship(cascade="all, delete-orphan")


class Rating(Base):
    __tablename__ = "calificaciones"
    __table_args__ = (CheckConstraint("stars BETWEEN 1 AND 5"),)
    recipe_id: Mapped[int] = mapped_column(
        ForeignKey("recetas.id", ondelete="CASCADE"), primary_key=True
    )
    stars: Mapped[int]
