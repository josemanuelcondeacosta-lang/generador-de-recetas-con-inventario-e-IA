import json

import pytest
from pydantic import ValidationError

from app.schemas import IngredientInput
from app.services import llm_service


RECIPE = {
    "titulo": "Arroz cocido", "ingredientes": ["100 g de arroz", "200 ml de agua"],
    "pasos": ["Hierve el agua y cocina el arroz."], "tiempo_minutos": 20, "dificultad": "fácil",
}


def test_prompt_includes_schema_and_inventory():
    item = IngredientInput(name="Arroz", quantity=100, unit="g")
    system, user = llm_service.build_messages([item])
    assert system["role"] == "system"
    assert "tiempo_minutos" in system["content"]
    assert json.loads(user["content"]) == [item.model_dump()]


def test_parser_accepts_complete_recipe():
    assert llm_service.parse_recipe(json.dumps(RECIPE)).model_dump() == RECIPE


@pytest.mark.parametrize("payload", ["texto libre", '{"titulo":"Arroz"}', json.dumps({**RECIPE, "tiempo_minutos": "20"})])
def test_parser_rejects_invalid_recipe(payload):
    with pytest.raises(ValidationError):
        llm_service.parse_recipe(payload)
