"""Page tests for the web template.

These pin the web type's contract through HTTP, the way the API
templates pin theirs: the page renders the sample slice, the
markup floor holds (landmarks, skip link, labelled control), the
add-item journey works end to end, and a server-only secret never
appears in any response.
"""

import importlib

import pytest
from fastapi.testclient import TestClient

import app.config
import app.main

client = TestClient(app.main.app)


def test_index_renders_items() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "First item" in response.text
    assert "Second item" in response.text


def test_markup_floor() -> None:
    response = client.get("/")
    assert '<html lang="en">' in response.text
    assert '<main id="main">' in response.text
    assert "Skip to main content" in response.text
    assert '<label for="item-name">' in response.text
    assert 'id="item-name"' in response.text


def test_add_item_journey() -> None:
    response = client.post("/items", data={"name": "Third item"}, follow_redirects=True)
    assert response.status_code == 200
    assert "Third item" in response.text


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_static_assets_served() -> None:
    response = client.get("/static/site.css")
    assert response.status_code == 200
    assert "skip-link" in response.text


def test_public_config_is_rendered() -> None:
    response = client.get("/")
    assert "{{ProjectName}}" in response.text


def test_server_secret_never_leaks(monkeypatch: pytest.MonkeyPatch) -> None:
    sentinel = "sentinel-secret-12345"
    prefix = app.config._PREFIX
    monkeypatch.setenv(prefix + "SERVER_API_KEY", sentinel)
    monkeypatch.setenv(prefix + "PUBLIC_APP_NAME", "Public Name")
    importlib.reload(app.config)
    importlib.reload(app.main)
    try:
        reloaded = TestClient(app.main.app)
        for path in ("/", "/health", "/static/site.css"):
            assert sentinel not in reloaded.get(path).text, path
        assert "Public Name" in reloaded.get("/").text
    finally:
        monkeypatch.undo()
        importlib.reload(app.config)
        importlib.reload(app.main)
