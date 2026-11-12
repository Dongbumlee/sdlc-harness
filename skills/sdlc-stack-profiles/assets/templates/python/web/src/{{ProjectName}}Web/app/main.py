"""The web app: server-rendered pages over the sample items slice.

Routes: `/` renders the items page, `POST /items` handles the add
form (post/redirect/get, so a refresh never resubmits), `/health`
answers the probe, `/static` serves assets. Only PublicConfig is
ever passed to a template — see app/config.py for the split.
"""

from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import load_public_config, load_server_config
from app.items import seeded_store

BASE_DIR = Path(__file__).parent

app = FastAPI(title="{{ProjectName}} web")
templates = Jinja2Templates(directory=BASE_DIR / "templates")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

store = seeded_store()
public = load_public_config()
# Held for server-side calls only. Never rendered: the test suite
# pins a sentinel value out of every response.
server = load_server_config()
_ = server


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "index.html",
        {"public": public, "items": store.list_items()},
    )


@app.post("/items")
def add_item(name: str = Form(...)) -> RedirectResponse:
    store.add(name.strip())
    return RedirectResponse("/", status_code=303)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
