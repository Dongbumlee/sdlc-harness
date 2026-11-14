// Copyright (c) {{Year}}. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root for license information.

//! Sample library crate: small text-normalization helpers.
//!
//! The public items of this crate are the library's API. CI checks them
//! against the last release with cargo-semver-checks and fails on
//! breaking changes; grow the surface deliberately.
//!
//! # Quickstart
//!
//! ```
//! use {{CrateName}}::{slugify, truncate};
//!
//! assert_eq!(slugify("Hello, World!"), "hello-world");
//! assert_eq!(truncate("a longer sentence", 6), "a lon…");
//! ```
//!
//! This quickstart is a doctest: `cargo test` executes it, so the
//! documented usage can never drift from the shipped API.

/// Converts `input` to a lowercase, hyphen-separated slug: alphanumeric
/// characters are kept, every other run of characters becomes one
/// hyphen, and leading/trailing hyphens are trimmed.
///
/// # Examples
///
/// ```
/// use {{CrateName}}::slugify;
///
/// assert_eq!(slugify("Hello, World!"), "hello-world");
/// ```
pub fn slugify(input: &str) -> String {
    let mut out = String::new();
    let mut last_hyphen = true; // trims leading separators
    for ch in input.chars() {
        if ch.is_alphanumeric() {
            out.extend(ch.to_lowercase());
            last_hyphen = false;
        } else if !last_hyphen {
            out.push('-');
            last_hyphen = true;
        }
    }
    out.trim_end_matches('-').to_string()
}

/// Shortens `input` to at most `max` characters, appending an ellipsis
/// when truncation occurs. A `max` of 0 returns an empty string.
///
/// # Examples
///
/// ```
/// use {{CrateName}}::truncate;
///
/// assert_eq!(truncate("a longer sentence", 6), "a lon…");
/// ```
pub fn truncate(input: &str, max: usize) -> String {
    if max == 0 {
        return String::new();
    }
    if input.chars().count() <= max {
        return input.to_string();
    }
    if max == 1 {
        return "…".to_string();
    }
    let head: String = input.chars().take(max - 1).collect();
    format!("{head}…")
}
