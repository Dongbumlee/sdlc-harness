// Copyright (c) {{Year}}. All rights reserved.
// Licensed under the MIT License. See LICENSE in the project root for license information.

//! The command tree over the textkit core. The command surface is a
//! contract (see the cli standard in the sdlc-stack-profiles skill):
//! data goes to stdout, diagnostics to stderr, and exit codes follow
//! the documented map — 0 success, 1 failure, 2 usage error. Clap's
//! own parse failures already exit 2 with the error on stderr; this
//! module maps everything else onto the same map.

use std::path::PathBuf;

use clap::{Parser, Subcommand};

use crate::output::{Format, Output};
use crate::textkit;

/// Exit codes — the documented map. Changes here are breaking changes.
pub const EXIT_OK: i32 = 0;
pub const EXIT_FAILURE: i32 = 1;
pub const EXIT_USAGE: i32 = 2;

const LONG_ABOUT: &str = "{{ProjectName}} is a sample command-line tool built from the rust/cli
template. It demonstrates the CLI contract: data goes to stdout,
diagnostics go to stderr, and the command surface (flags, output
schema, exit codes) is a tested API.

Exit codes:
  0  success
  1  failure (the command ran but could not complete)
  2  usage error (unknown command, bad flags, invalid arguments)

Configuration precedence: flags, then environment
(<PREFIX>_FORMAT and friends, where the prefix is the
upper-cased tool name), then defaults. Secrets are read from
the environment, never from flags.";

/// The root command. Global flags are available on every subcommand.
#[derive(Parser)]
#[command(name = "{{project-name}}", version, about = "{{ProjectName}} sample command-line tool", long_about = LONG_ABOUT)]
pub struct Cli {
    /// Output format for data commands: plain or json.
    #[arg(long, global = true, value_name = "FORMAT")]
    pub format: Option<String>,

    /// Shorthand for --format json.
    #[arg(long, global = true)]
    pub json: bool,

    /// Disable colour in diagnostics (NO_COLOR is also honoured).
    #[arg(long, global = true)]
    pub no_color: bool,

    /// Print diagnostics about what the command is doing.
    #[arg(long, global = true)]
    pub verbose: bool,

    /// Suppress diagnostics.
    #[arg(long, global = true)]
    pub quiet: bool,

    /// Never prompt; fail instead of asking.
    #[arg(long, global = true)]
    pub no_input: bool,

    /// Show what would happen without writing anything.
    #[arg(long, global = true)]
    pub dry_run: bool,

    #[command(subcommand)]
    pub command: Command,
}

#[derive(Subcommand)]
pub enum Command {
    /// Text transformations
    Text {
        #[command(subcommand)]
        verb: TextVerb,
    },
    /// Generate man pages for all commands (generated from the
    /// command tree itself, never written by hand)
    #[command(hide = true)]
    Man {
        /// Directory to write the pages into
        #[arg(default_value = "./man")]
        dir: PathBuf,
    },
    /// Print a shell completion script (bash, zsh, fish, powershell)
    #[command(hide = true)]
    Completions {
        #[arg(value_enum)]
        shell: clap_complete::Shell,
    },
}

#[derive(Subcommand)]
pub enum TextVerb {
    /// Convert text to a lowercase hyphenated slug
    Slugify {
        /// The text to convert
        #[arg(required = true, num_args = 1..)]
        text: Vec<String>,
        /// Write the result to this file instead of stdout
        #[arg(long, value_name = "PATH")]
        out: Option<PathBuf>,
        /// Overwrite the --out file if it exists
        #[arg(long)]
        force: bool,
    },
    /// Shorten text to at most --max characters
    Truncate {
        /// Maximum length in characters (including the ellipsis)
        #[arg(long, default_value_t = 40, value_name = "N")]
        max: usize,
        /// The text to shorten
        #[arg(required = true, num_args = 1..)]
        text: Vec<String>,
        /// Write the result to this file instead of stdout
        #[arg(long, value_name = "PATH")]
        out: Option<PathBuf>,
        /// Overwrite the --out file if it exists
        #[arg(long)]
        force: bool,
    },
}

/// Parses the arguments and runs the command, returning the process
/// exit code. Clap parse errors (and --help/--version) are handled
/// by clap itself, which prints to the right stream and exits with
/// the right code — 2 for usage errors, 0 for help and version.
pub fn run() -> i32 {
    let cli = match Cli::try_parse() {
        Ok(cli) => cli,
        Err(err) => err.exit(),
    };
    let output = match resolve_output(&cli) {
        Ok(output) => output,
        Err(message) => {
            eprintln!("Error: {message}");
            eprintln!("Run '{{project-name}} --help' for usage.");
            return EXIT_USAGE;
        }
    };
    match dispatch(&cli, &output) {
        Ok(()) => EXIT_OK,
        Err(err) => {
            eprintln!("Error: {err}");
            EXIT_FAILURE
        }
    }
}

/// Applies configuration precedence for the format setting: an
/// explicitly passed flag wins (including the --json shorthand),
/// then the environment, then the default.
fn resolve_output(cli: &Cli) -> Result<Output, String> {
    let prefix = env_prefix();
    let format = if cli.json {
        "json".to_string()
    } else if let Some(format) = &cli.format {
        format.clone()
    } else if let Ok(format) = std::env::var(format!("{prefix}FORMAT")) {
        format
    } else {
        "plain".to_string()
    };
    let format = match format.as_str() {
        "plain" => Format::Plain,
        "json" => Format::Json,
        other => return Err(format!("invalid format '{other}': want plain or json")),
    };
    Ok(Output::new(format, cli.no_color, cli.quiet))
}

/// The environment prefix derived from the tool name, upper-cased
/// with dashes turned into underscores (e.g. SAMPLE_).
fn env_prefix() -> String {
    let name = std::env::args()
        .next()
        .and_then(|arg0| {
            std::path::Path::new(&arg0)
                .file_name()
                .map(|n| n.to_string_lossy().into_owned())
        })
        .unwrap_or_else(|| "{{project-name}}".to_string());
    name.to_uppercase().replace('-', "_") + "_"
}

fn dispatch(cli: &Cli, output: &Output) -> Result<(), Box<dyn std::error::Error>> {
    match &cli.command {
        Command::Text { verb } => match verb {
            TextVerb::Slugify { text, out, force } => {
                let result = textkit::slugify(&text.join(" "));
                deliver(cli, output, &result, &[], out.as_deref(), *force)
            }
            TextVerb::Truncate {
                max,
                text,
                out,
                force,
            } => {
                if *max < 1 {
                    // A validation failure after parsing is still a
                    // usage error on the documented map.
                    eprintln!("Error: --max must be at least 1, got {max}");
                    eprintln!("Run '{{project-name}} --help' for usage.");
                    std::process::exit(EXIT_USAGE);
                }
                let input = text.join(" ");
                let result = textkit::truncate(&input, *max);
                let extra = [("truncated", serde_json::Value::Bool(result != input))];
                deliver(cli, output, &result, &extra, out.as_deref(), *force)
            }
        },
        Command::Man { dir } => {
            std::fs::create_dir_all(dir)?;
            let cmd = <Cli as clap::CommandFactory>::command();
            clap_mangen::generate_to(cmd, dir)?;
            Ok(())
        }
        Command::Completions { shell } => {
            let mut cmd = <Cli as clap::CommandFactory>::command();
            let name = cmd.get_name().to_string();
            clap_complete::generate(*shell, &mut cmd, name, &mut std::io::stdout());
            Ok(())
        }
    }
}

/// Routes a verb's result: to stdout by default, or to a file when
/// --out is set. File delivery honours the safety contract —
/// --dry-run writes nothing, an existing file is never overwritten
/// without --force, and the user is only ever prompted at a
/// terminal (and never with --no-input).
fn deliver(
    cli: &Cli,
    output: &Output,
    result: &str,
    extra: &[(&str, serde_json::Value)],
    out_path: Option<&std::path::Path>,
    force: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    let Some(path) = out_path else {
        output.result(result, extra)?;
        return Ok(());
    };
    if cli.dry_run {
        output.diagnostic(&format!(
            "dry-run: would write {} bytes to {}",
            result.len() + 1,
            path.display()
        ));
        return Ok(());
    }
    if path.exists() && !force {
        if cli.no_input || !crate::output::stdin_is_tty() {
            return Err(format!(
                "{} already exists (use --force to overwrite)",
                path.display()
            )
            .into());
        }
        eprint!("Overwrite {}? [y/N] ", path.display());
        let mut answer = String::new();
        std::io::stdin().read_line(&mut answer)?;
        if answer.trim().to_lowercase() != "y" {
            output.diagnostic(&format!("aborted; {} left unchanged", path.display()));
            return Ok(());
        }
    }
    std::fs::write(path, format!("{result}\n"))?;
    output.diagnostic(&format!("wrote {}", path.display()));
    Ok(())
}
