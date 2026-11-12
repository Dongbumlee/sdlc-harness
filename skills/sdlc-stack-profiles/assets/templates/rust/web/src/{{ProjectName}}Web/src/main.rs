//! Composition root: load configuration, build the app, serve.
//! Wiring only — no business logic lives here.

use {{CrateName}}_web::config;
use {{CrateName}}_web::items::ItemStore;
use {{CrateName}}_web::web::app;

#[tokio::main]
async fn main() {
    let public = config::load_public(&config::env_get);
    let server = config::load_server(&config::env_get);
    let router = app(ItemStore::seeded(), public, server);

    let port = std::env::var("PORT").unwrap_or_else(|_| "8080".to_string());
    let listener = tokio::net::TcpListener::bind(format!("0.0.0.0:{port}"))
        .await
        .expect("bind listener");
    println!("listening on :{port}");
    axum::serve(listener, router).await.expect("serve");
}
