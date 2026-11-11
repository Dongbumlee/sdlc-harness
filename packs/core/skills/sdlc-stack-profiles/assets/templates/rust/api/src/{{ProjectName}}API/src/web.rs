//! HTTP boundary: axum routing and handlers. Handlers depend on the
//! [`crate::service::ItemService`] trait only.

use std::sync::Arc;

use axum::extract::{Path, State};
use axum::http::StatusCode;
use axum::routing::{get, post};
use axum::{Json, Router};
use serde_json::{Value, json};

use crate::model::{Item, ItemCreate};
use crate::service::ItemService;

/// Shared handler state: the item service, wired by the composition
/// root.
#[derive(Clone)]
pub struct AppState {
    items: Arc<dyn ItemService>,
}

/// Builds the HTTP routing for the API. It is the only place routes are
/// registered, so tests exercise exactly what `main` serves.
pub fn router(items: Arc<dyn ItemService>) -> Router {
    Router::new()
        .route("/health", get(health))
        .route("/health/ready", get(ready))
        .route("/items", post(create_item).get(list_items))
        .route("/items/{id}", get(get_item))
        .with_state(AppState { items })
}

/// Liveness probe, mirroring the other bundled templates.
async fn health() -> Json<Value> {
    Json(json!({"status": "healthy"}))
}

/// Readiness probe, mirroring the other bundled templates.
async fn ready() -> Json<Value> {
    Json(json!({"status": "ready"}))
}

async fn create_item(
    State(state): State<AppState>,
    Json(request): Json<ItemCreate>,
) -> (StatusCode, Json<Value>) {
    if request.name.trim().is_empty() {
        return (
            StatusCode::BAD_REQUEST,
            Json(json!({"error": "name must not be blank"})),
        );
    }
    let item = state.items.create(&request.name);
    (StatusCode::CREATED, Json(json!(item)))
}

async fn list_items(State(state): State<AppState>) -> Json<Vec<Item>> {
    Json(state.items.list())
}

async fn get_item(State(state): State<AppState>, Path(id): Path<i64>) -> (StatusCode, Json<Value>) {
    match state.items.get(id) {
        Some(item) => (StatusCode::OK, Json(json!(item))),
        None => (
            StatusCode::NOT_FOUND,
            Json(json!({"error": "item not found"})),
        ),
    }
}
