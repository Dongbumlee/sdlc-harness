//! Page tests for the web template.
//!
//! These pin the web type's contract through HTTP, the way the
//! API templates pin theirs: the page renders the sample slice,
//! the markup floor holds (landmarks, skip link, labelled
//! control), the add-item journey works end to end, and a
//! server-only secret never appears in any response. Requests go
//! through the router with tower's oneshot — no socket, no
//! sleeping.

use std::collections::HashMap;

use axum::Router;
use axum::body::{Body, to_bytes};
use axum::http::{Request, StatusCode};
use tower::ServiceExt;

use {{CrateName}}_web::config::{load_public, load_server};
use {{CrateName}}_web::items::ItemStore;
use {{CrateName}}_web::web::app;

fn fixture_app(env: &HashMap<String, String>) -> Router {
    let get = |key: &str| env.get(key).cloned();
    app(ItemStore::seeded(), load_public(&get), load_server(&get))
}

async fn get(app: Router, path: &str) -> (StatusCode, String) {
    let response = app
        .oneshot(Request::builder().uri(path).body(Body::empty()).unwrap())
        .await
        .unwrap();
    let status = response.status();
    let bytes = to_bytes(response.into_body(), usize::MAX).await.unwrap();
    (status, String::from_utf8(bytes.to_vec()).unwrap())
}

#[tokio::test]
async fn index_renders_items() {
    let (status, body) = get(fixture_app(&HashMap::new()), "/").await;
    assert_eq!(status, StatusCode::OK);
    assert!(body.contains("First item"), "{body}");
    assert!(body.contains("Second item"), "{body}");
}

#[tokio::test]
async fn markup_floor_holds() {
    let (_, body) = get(fixture_app(&HashMap::new()), "/").await;
    for want in [
        "<html lang=\"en\">",
        "<main id=\"main\">",
        "Skip to main content",
        "<label for=\"item-name\">",
        "id=\"item-name\"",
    ] {
        assert!(body.contains(want), "missing {want} in {body}");
    }
}

#[tokio::test]
async fn add_item_journey() {
    let app = fixture_app(&HashMap::new());
    let response = app
        .clone()
        .oneshot(
            Request::builder()
                .method("POST")
                .uri("/items")
                .header("content-type", "application/x-www-form-urlencoded")
                .body(Body::from("name=Third+item"))
                .unwrap(),
        )
        .await
        .unwrap();
    assert_eq!(response.status(), StatusCode::SEE_OTHER);
    let (_, body) = get(app, "/").await;
    assert!(body.contains("Third item"), "{body}");
}

#[tokio::test]
async fn health_answers() {
    let (status, body) = get(fixture_app(&HashMap::new()), "/health").await;
    assert_eq!(status, StatusCode::OK);
    assert!(body.contains("\"status\":\"ok\""), "{body}");
}

#[tokio::test]
async fn static_assets_served() {
    let (status, body) = get(fixture_app(&HashMap::new()), "/static/site.css").await;
    assert_eq!(status, StatusCode::OK);
    assert!(body.contains("skip-link"), "{body}");
}

#[tokio::test]
async fn public_config_rendered_and_secret_never_leaks() {
    let mut env = HashMap::new();
    env.insert(
        "SAMPLE_PUBLIC_APP_NAME".to_string(),
        "Public Name".to_string(),
    );
    env.insert(
        "SAMPLE_SERVER_API_KEY".to_string(),
        "sentinel-secret-12345".to_string(),
    );
    let app = fixture_app(&env);
    let (_, body) = get(app.clone(), "/").await;
    assert!(body.contains("Public Name"), "{body}");
    for path in ["/", "/health", "/static/site.css"] {
        let (_, content) = get(app.clone(), path).await;
        assert!(
            !content.contains("sentinel-secret-12345"),
            "server secret leaked in {path}"
        );
    }
}
