//! Composition root for the {{ProjectName}} API binary: wires the
//! implementations and starts the HTTP server. Wiring only — no
//! business logic lives here.

use std::sync::Arc;

use {{CrateName}}::service::{DefaultItemService, InMemoryItemRepository};
use {{CrateName}}::web;

#[tokio::main]
async fn main() {
    let repository = Arc::new(InMemoryItemRepository::new());
    let items = Arc::new(DefaultItemService::new(repository));

    let port = std::env::var("PORT").unwrap_or_else(|_| "8080".to_string());
    let listener = tokio::net::TcpListener::bind(format!("0.0.0.0:{port}"))
        .await
        .expect("failed to bind the listener");
    println!("listening on :{port}");
    axum::serve(listener, web::router(items))
        .await
        .expect("server error");
}
