from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=500)]
Stars = Annotated[int, Field(strict=True, ge=1, le=5)]


class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class IngredientInput(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]
    quantity: float = Field(gt=0, le=1_000_000, allow_inf_nan=False)
    unit: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=30)]


class IngredientOutput(IngredientInput):
    model_config = ConfigDict(from_attributes=True)
    id: int


class RecipeContent(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    titulo: Text
    ingredientes: list[Text] = Field(min_length=1, max_length=30)
    pasos: list[Text] = Field(min_length=1, max_length=20)
    tiempo_minutos: int = Field(gt=0, le=1440)
    dificultad: Literal["fácil", "media", "difícil"]


class RecipeOutput(RecipeContent):
    id: int
    created_at: datetime
    stars: Stars | None = None


class RatingInput(BaseModel):
    stars: Stars
