//! Handler tests for the sample items slice, exercising the router
//! exactly as `main` serves it.

use std::sync::Arc;

use axum::Router;
use axum::body::{Body, to_bytes};
use axum::http::{Request, StatusCode};
use tower::ServiceExt;

use {{CrateName}}::model::Item;
use {{CrateName}}::service::{DefaultItemService, InMemoryItemRepository};
use {{CrateName}}::web;

fn app() -> Router {
    let repository = Arc::new(InMemoryItemRepository::new());
    web::router(Arc::new(DefaultItemService::new(repository)))
}

async fn body_json(response: axum::response::Response) -> serde_json::Value {
    let bytes = to_bytes(response.into_body(), usize::MAX)
        .await
        .expect("collect body");
    serde_json::from_slice(&bytes).expect("body is JSON")
}

async fn send(app: Router, request: Request<Body>) -> axum::response::Response {
    app.oneshot(request).await.expect("router responds")
}

fn get(path: &str) -> Request<Body> {
    Request::builder()
        .method("GET")
        .uri(path)
        .body(Body::empty())
        .expect("request builds")
}

fn post_json(path: &str, body: &str) -> Request<Body> {
    Request::builder()
        .method("POST")
        .uri(path)
        .header("content-type", "application/json")
        .body(Body::from(body.to_owned()))
        .expect("request builds")
}

#[tokio::test]
async fn health_endpoints() {
    let response = send(app(), get("/health")).await;
    assert_eq!(response.status(), StatusCode::OK);
    assert_eq!(body_json(response).await["status"], "healthy");

    let response = send(app(), get("/health/ready")).await;
    assert_eq!(response.status(), StatusCode::OK);
    assert_eq!(body_json(response).await["status"], "ready");
}

#[tokio::test]
async fn create_and_get_item() {
    let app = app();
    let response = send(app.clone(), post_json("/items", r#"{"name":"first"}"#)).await;
    assert_eq!(response.status(), StatusCode::CREATED);
    let created: Item =
        serde_json::from_value(body_json(response).await).expect("created item parses");
    assert_eq!(created.name, "first");

    let response = send(app, get(&format!("/items/{}", created.id))).await;
    assert_eq!(response.status(), StatusCode::OK);
    let fetched: Item =
        serde_json::from_value(body_json(response).await).expect("fetched item parses");
    assert_eq!(fetched, created);
}

#[tokio::test]
async fn get_missing_item_is_404() {
    let response = send(app(), get("/items/999")).await;
    assert_eq!(response.status(), StatusCode::NOT_FOUND);
}

#[tokio::test]
async fn create_blank_name_is_400() {
    let response = send(app(), post_json("/items", r#"{"name":"  "}"#)).await;
    assert_eq!(response.status(), StatusCode::BAD_REQUEST);
}

#[tokio::test]
async fn list_items_in_id_order() {
    let app = app();
    send(app.clone(), post_json("/items", r#"{"name":"one"}"#)).await;
    send(app.clone(), post_json("/items", r#"{"name":"two"}"#)).await;

    let response = send(app, get("/items")).await;
    assert_eq!(response.status(), StatusCode::OK);
    let items: Vec<Item> =
        serde_json::from_value(body_json(response).await).expect("item list parses");
    assert_eq!(items.len(), 2);
    assert_eq!(items[0].name, "one");
    assert_eq!(items[1].name, "two");
}
