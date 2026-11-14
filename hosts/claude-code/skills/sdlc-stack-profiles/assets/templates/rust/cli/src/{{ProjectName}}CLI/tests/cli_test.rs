// Copyright (c) {{Year}}. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root for license information.

//! Contract tests for the CLI surface: golden files pin the help
//! and primary outputs, and subprocess tests pin the exit-code map
//! and stream behaviour against the real binary. Regenerate goldens
//! deliberately with UPDATE_GOLDEN=1 cargo test and review the diff
//! like an API change.

use std::io::Write;
use std::path::PathBuf;
use std::process::{Command, Stdio};

use clap::CommandFactory;
use {{CrateName}}::cli::Cli;

fn golden(name: &str, actual: &str) {
    let path = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("tests/testdata")
        .join(format!("{name}.golden"));
    if std::env::var("UPDATE_GOLDEN").is_ok_and(|v| v == "1") {
        std::fs::write(&path, actual).unwrap();
        return;
    }
    let want = std::fs::read_to_string(&path).unwrap();
    assert_eq!(
        actual,
        want,
        "output drifted from golden {}",
        path.display()
    );
}

#[test]
fn golden_help_root() {
    let help = Cli::command().render_long_help().to_string();
    golden("help-root", &help);
}

#[test]
fn golden_help_text() {
    let mut cmd = Cli::command();
    let text = cmd.find_subcommand_mut("text").unwrap();
    let help = text.render_long_help().to_string();
    golden("help-text", &help);
}

#[test]
fn golden_version() {
    let version = Cli::command().render_version().to_string();
    golden("version", &version);
}

/// Runs the real binary and captures (exit code, stdout, stderr).
fn run_binary(args: &[&str], stdin: &str, envs: &[(&str, &str)]) -> (i32, String, String) {
    let mut child = Command::new(env!("CARGO_BIN_EXE_{{project-name}}"))
        .args(args)
        .envs(envs.iter().copied())
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .unwrap();
    child
        .stdin
        .as_mut()
        .unwrap()
        .write_all(stdin.as_bytes())
        .unwrap();
    let out = child.wait_with_output().unwrap();
    (
        out.status.code().unwrap(),
        String::from_utf8(out.stdout).unwrap(),
        String::from_utf8(out.stderr).unwrap(),
    )
}

#[test]
fn golden_primary_outputs() {
    let (_, stdout, _) = run_binary(&["text", "slugify", "Hello, World!"], "", &[]);
    golden("slugify", &stdout);
    let (_, stdout, _) = run_binary(&["text", "slugify", "--json", "Hello, World!"], "", &[]);
    golden("slugify-json", &stdout);
    let (_, stdout, _) = run_binary(
        &["text", "truncate", "--max", "6", "a longer sentence"],
        "",
        &[],
    );
    golden("truncate", &stdout);
    let (_, stdout, _) = run_binary(
        &[
            "text",
            "truncate",
            "--max",
            "6",
            "--json",
            "a longer sentence",
        ],
        "",
        &[],
    );
    golden("truncate-json", &stdout);
}

// Exit-code tests: each failure mode maps to the documented code.
#[test]
fn exit_codes() {
    let cases: &[(&[&str], i32)] = &[
        (&["text", "slugify", "Hello"], 0),
        (&["frobnicate"], 2),
        (&["text", "slugify"], 2),
        (&["text", "truncate", "--max", "abc", "text"], 2),
        (&["text", "truncate", "--max", "0", "text"], 2),
        (&["--format", "yaml", "text", "slugify", "Hi"], 2),
        (
            &["text", "slugify", "--out", "/nonexistent-dir/x.txt", "Hi"],
            1,
        ),
    ];
    for (args, want) in cases {
        let (code, _, _) = run_binary(args, "", &[]);
        assert_eq!(code, *want, "args {args:?}");
    }
}

// Configuration precedence: flags beat the environment, the
// environment beats the default.
#[test]
fn format_precedence() {
    let (_, stdout, _) = run_binary(
        &["text", "slugify", "Hi There"],
        "",
        &[("SAMPLE_FORMAT", "json")],
    );
    assert!(stdout.starts_with('{'), "env format not applied: {stdout}");
    let (_, stdout, _) = run_binary(
        &["--format", "plain", "text", "slugify", "Hi There"],
        "",
        &[("SAMPLE_FORMAT", "json")],
    );
    assert_eq!(stdout, "hi-there\n", "flag should beat env");
}

// File delivery: dry-run writes nothing, an existing file is not
// overwritten without --force (and never prompts a non-terminal),
// --force overwrites.
#[test]
fn file_delivery() {
    let dir = std::env::temp_dir().join(format!("{{project-name}}-cli-test-{}", std::process::id()));
    std::fs::create_dir_all(&dir).unwrap();
    let target = dir.join("out.txt");
    let target = target.to_str().unwrap();

    let (code, _, _) = run_binary(
        &[
            "text",
            "slugify",
            "--dry-run",
            "--out",
            target,
            "Hello World",
        ],
        "",
        &[],
    );
    assert_eq!(code, 0);
    assert!(
        !std::path::Path::new(target).exists(),
        "dry-run must not write the file"
    );

    let (code, _, _) = run_binary(
        &["text", "slugify", "--out", target, "Hello World"],
        "",
        &[],
    );
    assert_eq!(code, 0);
    assert_eq!(std::fs::read_to_string(target).unwrap(), "hello-world\n");

    let (code, _, _) = run_binary(
        &["text", "slugify", "--out", target, "Changed Text"],
        "",
        &[],
    );
    assert_eq!(code, 1, "overwrite without --force");
    assert_eq!(std::fs::read_to_string(target).unwrap(), "hello-world\n");

    let (code, _, _) = run_binary(
        &[
            "text",
            "slugify",
            "--out",
            target,
            "--force",
            "Changed Text",
        ],
        "",
        &[],
    );
    assert_eq!(code, 0);
    assert_eq!(std::fs::read_to_string(target).unwrap(), "changed-text\n");

    std::fs::remove_dir_all(&dir).unwrap();
}
