from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.database import DB
from app.models import Ingredient, User
from app.schemas import IngredientInput, IngredientOutput
from app.security import CurrentUser

router = APIRouter(prefix="/api/ingredients", tags=["Ingredientes"])


def own_ingredient(ingredient_id: int, user: User, db: DB) -> Ingredient:
    item = db.scalar(select(Ingredient).where(
        Ingredient.id == ingredient_id, Ingredient.user_id == user.id
    ))
    if item is None:
        raise HTTPException(404, "Ingrediente no encontrado")
    return item


def save(item: Ingredient, data: IngredientInput, db: DB) -> Ingredient:
    item.name = data.name
    item.normalized_name = data.name.casefold()
    item.quantity = data.quantity
    item.unit = data.unit
    db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "El ingrediente ya existe en tu inventario") from None
    return item


@router.get("", response_model=list[IngredientOutput])
def list_ingredients(user: CurrentUser, db: DB):
    return db.scalars(select(Ingredient).where(
        Ingredient.user_id == user.id
    ).order_by(Ingredient.normalized_name)).all()


@router.post("", response_model=IngredientOutput, status_code=201)
def create_ingredient(data: IngredientInput, user: CurrentUser, db: DB):
    return save(Ingredient(user_id=user.id), data, db)


@router.get("/{ingredient_id}", response_model=IngredientOutput)
def read_ingredient(ingredient_id: int, user: CurrentUser, db: DB):
    return own_ingredient(ingredient_id, user, db)


@router.put("/{ingredient_id}", response_model=IngredientOutput)
def update_ingredient(ingredient_id: int, data: IngredientInput, user: CurrentUser, db: DB):
    return save(own_ingredient(ingredient_id, user, db), data, db)


@router.delete("/{ingredient_id}", status_code=204)
def delete_ingredient(ingredient_id: int, user: CurrentUser, db: DB):
    db.delete(own_ingredient(ingredient_id, user, db))
    db.commit()
