from app.schemas import RecipeContent
from app.services import llm_service
from test_llm import RECIPE


def test_login_protects_inventory(client, account):
    account()
    assert client.get("/api/ingredients").status_code == 401
    response = client.post("/api/auth/login", json={
        "email": "estudiante@example.com", "password": "contraseña de prueba",
    })
    assert response.status_code == 200
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    assert client.get("/api/ingredients", headers=headers).json() == []


def test_ingredient_crud_is_private(client, account):
    owner = account()
    other = account("otra@example.com")
    item = {"name": "Arroz", "quantity": 100, "unit": "g"}
    response = client.post("/api/ingredients", headers=owner, json=item)
    assert response.status_code == 201
    path = f"/api/ingredients/{response.json()['id']}"
    assert client.post("/api/ingredients", headers=owner, json={**item, "name": "arroz"}).status_code == 409
    assert client.get(path, headers=other).status_code == 404
    assert client.put(path, headers=owner, json={**item, "quantity": 50}).json()["quantity"] == 50
    assert client.delete(path, headers=owner).status_code == 204
    assert client.get(path, headers=owner).status_code == 404


def test_recipe_generation_rating_and_deletion(client, account, monkeypatch):
    owner = account()
    other = account("otra@example.com")
    assert client.post("/api/recipes/generate", headers=owner).status_code == 400
    for name, quantity, unit in [("Arroz", 100, "g"), ("Agua", 200, "ml")]:
        assert client.post("/api/ingredients", headers=owner, json={
            "name": name, "quantity": quantity, "unit": unit,
        }).status_code == 201

    def generate(inventory):
        assert [item.name for item in inventory] == ["Arroz", "Agua"]
        return RecipeContent(**RECIPE)

    monkeypatch.setattr(llm_service, "generate_recipe", generate)
    result = client.post("/api/recipes/generate", headers=owner)
    assert result.status_code == 201
    recipe = result.json()
    assert client.get("/api/recipes", headers=owner).json() == [recipe]
    assert client.get("/api/recipes", headers=other).json() == []
    path = f"/api/recipes/{recipe['id']}"
    assert client.put(path + "/rating", headers=other, json={"stars": 5}).status_code == 404
    for stars in [5, 4]:
        assert client.put(path + "/rating", headers=owner, json={"stars": stars}).json()["stars"] == stars
    assert client.delete(path, headers=other).status_code == 404
    assert client.delete(path, headers=owner).status_code == 204
    assert client.get("/api/recipes", headers=owner).json() == []
