//! Architecture conformance test: the profile's dependency direction
//! (web -> service -> model) is enforced mechanically by scanning the
//! crate's `use` statements, so a layering violation fails the test
//! run instead of waiting for a reviewer to notice it.

use std::fs;
use std::path::PathBuf;

/// Layers and the layers they must never depend on.
const FORBIDDEN: [(&str, &[&str]); 3] = [
    ("model", &["service", "web"]),
    ("service", &["web"]),
    ("web", &[] as &[&str]),
];

fn source(layer: &str) -> String {
    let path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("src")
        .join(format!("{layer}.rs"));
    fs::read_to_string(&path).unwrap_or_else(|err| panic!("read {}: {err}", path.display()))
}

#[test]
fn dependency_direction() {
    let mut violations = Vec::new();
    for (layer, banned) in FORBIDDEN {
        let text = source(layer);
        for line in text.lines() {
            let line = line.trim();
            if !line.starts_with("use crate::") {
                continue;
            }
            for target in banned {
                if line.starts_with(&format!("use crate::{target}")) {
                    violations.push(format!("{layer}.rs imports crate::{target}: {line}"));
                }
            }
        }
    }
    assert!(
        violations.is_empty(),
        "Layering violations:\n{}",
        violations.join("\n")
    );
}
