// Copyright (c) {{Year}}. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root for license information.

//! Black-box tests: this file imports the crate exactly as a consumer
//! does and exercises only the public API. Referencing every public
//! item here also pins the surface — removing or renaming an item
//! breaks this test's compilation before it can break a consumer.

use {{CrateName}}::{slugify, truncate};

#[test]
fn slugify_cases() {
    assert_eq!(slugify("Hello, World!"), "hello-world");
    assert_eq!(slugify("  spaced   out "), "spaced-out");
    assert_eq!(slugify("Rust 1.85"), "rust-1-85");
    assert_eq!(slugify(""), "");
    assert_eq!(slugify("!!!"), "");
}

#[test]
fn truncate_cases() {
    assert_eq!(truncate("short", 10), "short");
    assert_eq!(truncate("a longer sentence", 6), "a lon…");
    assert_eq!(truncate("anything", 0), "");
    assert_eq!(truncate("éclair", 3), "éc…");
}
