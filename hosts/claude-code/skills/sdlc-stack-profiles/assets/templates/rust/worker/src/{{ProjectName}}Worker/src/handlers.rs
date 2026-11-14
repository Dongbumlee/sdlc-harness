//! Sample handlers. Replace with your own job types; the contract
//! is what matters: return the effect's result string, return
//! [`JobError::Permanent`] for payloads that can never succeed, and
//! let everything else surface as retryable.

use std::collections::HashMap;

use serde_json::Value;

use crate::worker::{Handler, JobError};

/// Turn payload.text into a slug — the sample job's effect.
/// Lowercase, letters and digits kept, every other run of
/// characters becomes one hyphen, leading/trailing hyphens
/// trimmed — the same sample semantics as the other bundled
/// templates.
pub fn slugify(payload: &Value) -> Result<String, JobError> {
    let text = payload.get("text").and_then(Value::as_str).unwrap_or("");
    if text.trim().is_empty() {
        return Err(JobError::Permanent(
            "payload.text must be a non-empty string".to_string(),
        ));
    }
    let mut slug = String::new();
    let mut last_hyphen = true; // trims leading separators
    for ch in text.to_lowercase().chars() {
        if ch.is_alphanumeric() {
            slug.push(ch);
            last_hyphen = false;
        } else if !last_hyphen {
            slug.push('-');
            last_hyphen = true;
        }
    }
    Ok(slug.trim_end_matches('-').to_string())
}

/// The handler set for this worker.
pub fn handlers() -> HashMap<String, Handler> {
    let mut handlers: HashMap<String, Handler> = HashMap::new();
    handlers.insert("slugify".to_string(), Box::new(slugify));
    handlers
}
