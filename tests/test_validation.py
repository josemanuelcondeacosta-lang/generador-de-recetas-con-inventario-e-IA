import pytest
from pydantic import ValidationError

from app.schemas import IngredientInput, RatingInput


@pytest.mark.parametrize("quantity", [0, -1, float("inf")])
def test_ingredient_rejects_invalid_quantity(quantity):
    with pytest.raises(ValidationError):
        IngredientInput(name="Arroz", quantity=quantity, unit="g")


@pytest.mark.parametrize("stars", [0, 6, "5"])
def test_rating_requires_integer_from_one_to_five(stars):
    with pytest.raises(ValidationError):
        RatingInput(stars=stars)
