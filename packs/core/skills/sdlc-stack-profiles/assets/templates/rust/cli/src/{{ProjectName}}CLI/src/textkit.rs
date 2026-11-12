// Copyright (c) {{Year}}. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root for license information.

//! The CLI's library core: the testable logic lives here, free of
//! argument parsing and I/O, and the commands in [`crate::cli`] are
//! a thin shell over it.

/// Converts `s` to a lowercase, hyphen-separated slug: letters and
/// digits are kept, every other run of characters becomes one hyphen,
/// and leading/trailing hyphens are trimmed.
///
/// ```
/// use {{CrateName}}::textkit::slugify;
///
/// assert_eq!(slugify("Hello, World!"), "hello-world");
/// ```
pub fn slugify(s: &str) -> String {
    let mut out = String::new();
    let mut last_hyphen = true; // trims leading separators
    for c in s.chars() {
        if c.is_alphanumeric() {
            out.extend(c.to_lowercase());
            last_hyphen = false;
        } else if !last_hyphen {
            out.push('-');
            last_hyphen = true;
        }
    }
    out.trim_end_matches('-').to_string()
}

/// Shortens `s` to at most `max` characters, appending an ellipsis
/// when truncation occurs. A `max` below 1 returns an empty string.
///
/// ```
/// use {{CrateName}}::textkit::truncate;
///
/// assert_eq!(truncate("a longer sentence", 6), "a lon…");
/// ```
pub fn truncate(s: &str, max: usize) -> String {
    if max < 1 {
        return String::new();
    }
    let chars: Vec<char> = s.chars().collect();
    if chars.len() <= max {
        return s.to_string();
    }
    if max == 1 {
        return "…".to_string();
    }
    let mut out: String = chars[..max - 1].iter().collect();
    out.push('…');
    out
}
