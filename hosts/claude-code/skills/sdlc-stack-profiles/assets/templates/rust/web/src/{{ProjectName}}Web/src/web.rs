//! The HTTP boundary: server-rendered pages over the sample
//! items slice.
//!
//! Routes: `GET /` renders the items page, `POST /items` handles
//! the add form (post/redirect/get, so a refresh never
//! resubmits), `GET /health` answers the probe, and
//! `GET /static/site.css` serves the stylesheet. Only
//! [`PublicConfig`] is ever passed to a template — see the
//! config module for the split. Templates are MiniJinja with
//! autoescaping for `.html`, so rendered values are escaped by
//! construction.

use std::sync::{Arc, Mutex};

use axum::Form;
use axum::Router;
use axum::extract::State;
use axum::response::{Html, IntoResponse, Json, Redirect};
use axum::routing::get;
use minijinja::{Environment, context};
use serde::Deserialize;

use crate::config::{PublicConfig, ServerConfig};
use crate::items::ItemStore;

const SITE_CSS: &str = include_str!("../templates/site.css");

/// Shared application state.
#[derive(Clone)]
pub struct AppState {
    store: Arc<Mutex<ItemStore>>,
    public: Arc<PublicConfig>,
    /// Held for server-side calls only; intentionally never
    /// rendered — the allow is the boundary made visible.
    #[allow(dead_code)]
    server: Arc<ServerConfig>,
    templates: Arc<Environment<'static>>,
}

/// Build the application with its routes.
pub fn app(store: ItemStore, public: PublicConfig, server: ServerConfig) -> Router {
    let mut env = Environment::new();
    env.add_template_owned(
        "base.html".to_string(),
        include_str!("../templates/base.html").to_string(),
    )
    .expect("base template parses");
    env.add_template_owned(
        "index.html".to_string(),
        include_str!("../templates/index.html").to_string(),
    )
    .expect("index template parses");
    let state = AppState {
        store: Arc::new(Mutex::new(store)),
        public: Arc::new(public),
        server: Arc::new(server),
        templates: Arc::new(env),
    };
    Router::new()
        .route("/", get(index))
        .route("/items", axum::routing::post(add_item))
        .route("/health", get(health))
        .route("/static/site.css", get(site_css))
        .with_state(state)
}

async fn index(State(state): State<AppState>) -> impl IntoResponse {
    let items = state.store.lock().expect("store lock").list();
    let template = state
        .templates
        .get_template("index.html")
        .expect("index template");
    let rendered = template
        .render(context! {
            public => state.public.as_ref(),
            items => items,
        })
        .expect("index renders");
    Html(rendered)
}

#[derive(Deserialize)]
struct AddItemForm {
    name: String,
}

async fn add_item(
    State(state): State<AppState>,
    Form(form): Form<AddItemForm>,
) -> impl IntoResponse {
    let name = form.name.trim();
    if !name.is_empty() {
        state.store.lock().expect("store lock").add(name);
    }
    Redirect::to("/")
}

async fn health() -> impl IntoResponse {
    Json(serde_json::json!({"status": "ok"}))
}

async fn site_css() -> impl IntoResponse {
    ([("content-type", "text/css; charset=utf-8")], SITE_CSS)
}
