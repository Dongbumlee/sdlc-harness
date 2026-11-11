import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

# Shared test helpers: pytest runs with --import-mode=importlib (see
# pyproject.toml), under which test modules cannot import this
# conftest. The line below puts tests/ on sys.path so shared helpers
# can live in a plain module here (e.g. tests/rig.py with fixture
# factories and scenario builders) and be imported by name from any
# test module. Keep this file to fixture definitions; do not import
# conftest itself.
sys.path.insert(0, str(Path(__file__).parent))


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client
