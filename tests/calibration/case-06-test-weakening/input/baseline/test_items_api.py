from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_item_returns_201():
    response = client.post("/items", json={"name": "alpha"})
    assert response.status_code == 201
    assert response.json()["name"] == "alpha"


def test_create_item_empty_name_returns_422():
    response = client.post("/items", json={"name": ""})
    assert response.status_code == 422
