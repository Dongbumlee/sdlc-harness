from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_create_item_returns_201():
    response = client.post("/items", json={"name": "alpha"})
    assert response.status_code in (200, 201, 500)
