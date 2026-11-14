// Copyright (c) {{Year}}. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root for license information.

//! The stream contract: results on stdout (plain or JSON),
//! diagnostics on stderr, and colour only where a human is looking
//! at a terminal — never in piped data.

use std::io::{IsTerminal, Write};

/// The resolved output format for data commands.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Format {
    Plain,
    Json,
}

/// Owns printing for one execution, under the resolved options.
pub struct Output {
    format: Format,
    color: bool,
    quiet: bool,
}

impl Output {
    pub fn new(format: Format, no_color: bool, quiet: bool) -> Self {
        Self {
            format,
            color: color_enabled(no_color),
            quiet,
        }
    }

    pub fn format(&self) -> Format {
        self.format
    }

    /// Prints a command's primary data to stdout. In JSON mode the
    /// value is wrapped in an object with a stable `result` field;
    /// callers may add fields but the shape never changes within a
    /// major version.
    pub fn result(&self, value: &str, extra: &[(&str, serde_json::Value)]) -> std::io::Result<()> {
        let mut stdout = std::io::stdout().lock();
        match self.format {
            Format::Json => {
                let mut payload = serde_json::Map::new();
                payload.insert(
                    "result".to_string(),
                    serde_json::Value::String(value.to_string()),
                );
                for (k, v) in extra {
                    payload.insert((*k).to_string(), v.clone());
                }
                writeln!(stdout, "{}", serde_json::Value::Object(payload))
            }
            Format::Plain => writeln!(stdout, "{value}"),
        }
    }

    /// Prints a human-only note to stderr, unless `--quiet`.
    /// Diagnostics never carry primary data.
    pub fn diagnostic(&self, message: &str) {
        if self.quiet {
            return;
        }
        let mut stderr = std::io::stderr().lock();
        if self.color {
            let _ = writeln!(stderr, "\u{1b}[2m{message}\u{1b}[0m");
        } else {
            let _ = writeln!(stderr, "{message}");
        }
    }
}

/// Decides whether styled diagnostics are appropriate: an explicit
/// `--no-color` or the `NO_COLOR` environment variable wins, and
/// colour is only ever used on a terminal.
pub fn color_enabled(no_color_flag: bool) -> bool {
    if no_color_flag {
        return false;
    }
    if std::env::var_os("NO_COLOR").is_some() {
        return false;
    }
    std::io::stdout().is_terminal()
}

/// Reports whether stdin is a terminal — the only situation in
/// which prompting is allowed.
pub fn stdin_is_tty() -> bool {
    std::io::stdin().is_terminal()
}
