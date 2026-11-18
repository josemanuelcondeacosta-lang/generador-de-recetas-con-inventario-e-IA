from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import DB
from app.models import Ingredient, Rating, Recipe, User
from app.schemas import IngredientInput, RatingInput, RecipeOutput
from app.security import CurrentUser
from app.services import llm_service

router = APIRouter(prefix="/api/recipes", tags=["Recetas"])


def output(recipe: Recipe) -> RecipeOutput:
    return RecipeOutput(
        **recipe.content,
        id=recipe.id,
        created_at=recipe.created_at,
        stars=recipe.rating.stars if recipe.rating else None,
    )


def own_recipe(recipe_id: int, user: User, db: DB) -> Recipe:
    recipe = db.scalar(select(Recipe).where(
        Recipe.id == recipe_id, Recipe.user_id == user.id
    ).with_for_update())
    if recipe is None:
        raise HTTPException(404, "Receta no encontrada")
    return recipe


@router.get("", response_model=list[RecipeOutput])
def history(user: CurrentUser, db: DB):
    recipes = db.scalars(select(Recipe).where(Recipe.user_id == user.id)
                         .options(selectinload(Recipe.rating)).order_by(Recipe.id.desc()))
    return [output(recipe) for recipe in recipes]


@router.post("/generate", response_model=RecipeOutput, status_code=201)
def generate(user: CurrentUser, db: DB):
    user_id = user.id
    ingredients = db.scalars(select(Ingredient).where(
        Ingredient.user_id == user_id
    ).order_by(Ingredient.id)).all()
    inventory = [
        IngredientInput(name=item.name, quantity=item.quantity, unit=item.unit)
        for item in ingredients
    ]
    if not inventory:
        raise HTTPException(400, "Agrega al menos un ingrediente antes de generar")
    db.rollback()  # Release the database connection during the external request.
    try:
        content = llm_service.generate_recipe(inventory)
    except llm_service.LLMUnavailable:
        raise HTTPException(503, "La generación todavía no está configurada") from None
    except llm_service.LLMError:
        raise HTTPException(502, "El proveedor no devolvió una receta válida. Intenta de nuevo.") from None
    recipe = Recipe(user_id=user_id, content=content.model_dump())
    db.add(recipe)
    db.commit()
    return output(recipe)


@router.put("/{recipe_id}/rating", response_model=RecipeOutput)
def rate(recipe_id: int, data: RatingInput, user: CurrentUser, db: DB):
    recipe = own_recipe(recipe_id, user, db)
    if recipe.rating is None:
        recipe.rating = Rating(stars=data.stars)
    else:
        recipe.rating.stars = data.stars
    db.commit()
    return output(recipe)


@router.delete("/{recipe_id}", status_code=204)
def delete(recipe_id: int, user: CurrentUser, db: DB):
    db.delete(own_recipe(recipe_id, user, db))
    db.commit()
