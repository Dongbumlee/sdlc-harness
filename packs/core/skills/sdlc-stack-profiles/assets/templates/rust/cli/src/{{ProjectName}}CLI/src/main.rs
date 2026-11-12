// Copyright (c) {{Year}}. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root for license information.

//! Thin entry point: all behaviour lives in the library
//! ([`{{CrateName}}::cli`]) over the textkit core, so the logic is
//! importable and testable without the binary.

fn main() {
    std::process::exit({{CrateName}}::cli::run());
}
