def test_create_and_get_item(client):
    created = client.post("/items", json={"name": "first", "description": "sample"})
    assert created.status_code == 201
    body = created.json()
    assert body["name"] == "first"

    fetched = client.get(f"/items/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "first"


def test_list_items(client):
    client.post("/items", json={"name": "listed"})
    response = client.get("/items")
    assert response.status_code == 200
    assert any(item["name"] == "listed" for item in response.json())


def test_get_unknown_item_returns_404(client):
    response = client.get("/items/999999")
    assert response.status_code == 404


def test_create_item_requires_name(client):
    response = client.post("/items", json={"name": ""})
    assert response.status_code == 422
