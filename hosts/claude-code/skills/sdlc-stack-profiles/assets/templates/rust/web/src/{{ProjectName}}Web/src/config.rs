//! Application configuration, split the way the web type
//! requires.
//!
//! The split is structural, not a naming habit. Values a browser
//! may see live in [`PublicConfig`] and are the only ones
//! templates ever receive. Server-only values live in
//! [`ServerConfig`], are read from the environment at startup,
//! and must never be rendered, logged, or sent to a client —
//! leaking one into a page is this type's signature security
//! defect, and the test suite pins a sentinel secret out of every
//! response.
//!
//! The environment is read through an injected getter so tests
//! supply a map instead of mutating process state.

/// Browser-safe values: fine to render into any page.
#[derive(Debug, Clone, serde::Serialize)]
pub struct PublicConfig {
    pub app_name: String,
}

/// Server-only values: never rendered, never sent to a client.
#[derive(Debug, Clone)]
pub struct ServerConfig {
    pub api_key: String,
}

fn prefix() -> String {
    "{{project-name}}".to_uppercase().replace('-', "_") + "_"
}

/// Load the public configuration through `get` (an environment
/// lookup in production, a fixture map in tests).
pub fn load_public(get: &dyn Fn(&str) -> Option<String>) -> PublicConfig {
    let app_name = get(&(prefix() + "PUBLIC_APP_NAME"))
        .filter(|v| !v.is_empty())
        .unwrap_or_else(|| "{{ProjectName}}".to_string());
    PublicConfig { app_name }
}

/// Load the server-only configuration through `get`.
pub fn load_server(get: &dyn Fn(&str) -> Option<String>) -> ServerConfig {
    ServerConfig {
        api_key: get(&(prefix() + "SERVER_API_KEY")).unwrap_or_default(),
    }
}

/// The production getter: the process environment.
pub fn env_get(key: &str) -> Option<String> {
    std::env::var(key).ok()
}
