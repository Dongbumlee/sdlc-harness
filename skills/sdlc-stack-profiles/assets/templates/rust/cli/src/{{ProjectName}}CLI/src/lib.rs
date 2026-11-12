// Copyright (c) {{Year}}. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root for license information.

//! {{ProjectName}} sample command-line tool.
//!
//! The library core of the CLI: [`textkit`] holds the testable logic,
//! [`cli`] builds the command tree over it, and the binary in main.rs
//! is a thin entry point — everything is importable and testable
//! without the binary.

pub mod cli;
pub mod output;
pub mod textkit;
