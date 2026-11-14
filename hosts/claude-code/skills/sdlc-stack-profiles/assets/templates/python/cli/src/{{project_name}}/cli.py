"""The command tree over the textkit core.

The command surface is a contract (see the cli standard in the
sdlc-stack-profiles skill): data goes to stdout, diagnostics to
stderr, and exit codes follow the documented map — 0 success,
1 failure, 2 usage error. Click's own semantics already implement
the map: UsageError exits 2, ClickException exits 1, and both print
to stderr.

Global options may be given at any level of the tree
(`tool --json text slugify`, `tool text --json slugify`, and
`tool text slugify --json` are equivalent): Click parses each level
separately, so every level carries the options and merges what was
explicitly set there into the shared `Globals`; the innermost
explicit value wins per option.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

import click
from click.shell_completion import get_completion_class

from {{project_name}} import textkit
from {{project_name}}.output import Output

LONG_HELP = """{{ProjectName}} is a sample command-line tool built from the python/cli
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
the environment, never from flags."""


@dataclass
class Globals:
    """Global option values merged across the command tree.

    Each level overwrites only the options explicitly set at that
    level (Click reports the source of every parameter), so the
    innermost explicit value wins per option.
    """

    format_: str = "plain"
    format_set: bool = False
    json_flag: bool = False
    no_color: bool = False
    verbose: bool = False
    quiet: bool = False
    no_input: bool = False
    dry_run: bool = False


@dataclass
class State:
    """The resolved settings for one leaf command."""

    output: Output
    no_input: bool
    dry_run: bool


_GLOBAL_OPTIONS = [
    click.option(
        "--format",
        "format_",
        default="plain",
        metavar="FORMAT",
        help="Output format for data commands: plain or json.",
    ),
    click.option(
        "--json", "json_flag", is_flag=True, help="Shorthand for --format json."
    ),
    click.option(
        "--no-color",
        is_flag=True,
        help="Disable colour in diagnostics (NO_COLOR is also honoured).",
    ),
    click.option(
        "--verbose",
        is_flag=True,
        help="Print diagnostics about what the command is doing.",
    ),
    click.option("--quiet", is_flag=True, help="Suppress diagnostics."),
    click.option(
        "--no-input", is_flag=True, help="Never prompt; fail instead of asking."
    ),
    click.option(
        "--dry-run",
        is_flag=True,
        help="Show what would happen without writing anything.",
    ),
]


def global_options(fn):
    """Attach the global options to a group or command at any level."""
    for option in reversed(_GLOBAL_OPTIONS):
        fn = option(fn)
    return fn


def _merge_globals(ctx: click.Context, kwargs: dict) -> Globals:
    """Merge one level's explicit global options into ctx.obj."""
    merged: Globals = ctx.find_object(Globals) or Globals()
    commandline = click.core.ParameterSource.COMMANDLINE
    for name, value in kwargs.items():
        if ctx.get_parameter_source(name) == commandline:
            setattr(merged, name, value)
            if name == "format_":
                merged.format_set = True
                merged.json_flag = False
            elif name == "json_flag":
                merged.format_set = True
    ctx.obj = merged
    return merged


def _resolve_state(merged: Globals) -> State:
    """Apply configuration precedence and build the leaf State.

    Flags (the merged explicit values) win, then the environment,
    then defaults.
    """
    if merged.json_flag:
        resolved = "json"
    elif merged.format_set:
        resolved = merged.format_
    else:
        resolved = os.environ.get(_env_prefix() + "FORMAT", merged.format_)
    if resolved not in ("plain", "json"):
        raise click.UsageError(f"invalid format '{resolved}': want plain or json")
    return State(
        output=Output(resolved, merged.no_color, merged.quiet),
        no_input=merged.no_input,
        dry_run=merged.dry_run,
    )


def _env_prefix() -> str:
    """The environment prefix derived from the tool name."""
    return "{{project-name}}".upper().replace("-", "_") + "_"


@click.group(name="{{project-name}}", help=LONG_HELP)
@click.version_option(package_name="{{project-name}}")
@global_options
@click.pass_context
def cli(ctx: click.Context, **kwargs) -> None:
    """{{ProjectName}} sample command-line tool."""
    _merge_globals(ctx, kwargs)


@cli.group(help="Text transformations over the textkit core.")
@global_options
@click.pass_context
def text(ctx: click.Context, **kwargs) -> None:
    """Text transformations."""
    _merge_globals(ctx, kwargs)


def _deliver(
    state: State,
    result: str,
    extra: dict | None,
    out: Path | None,
    force: bool,
) -> None:
    """Route a verb's result: stdout by default, or a file with --out.

    File delivery honours the safety contract — --dry-run writes
    nothing, an existing file is never overwritten without --force,
    and the user is only ever prompted at a terminal (and never
    with --no-input).
    """
    output = state.output
    if out is None:
        output.result(result, extra)
        return
    if state.dry_run:
        output.diagnostic(f"dry-run: would write {len(result) + 1} bytes to {out}")
        return
    if out.exists() and not force:
        if state.no_input or not sys.stdin.isatty():
            raise click.ClickException(
                f"{out} already exists (use --force to overwrite)"
            )
        if not click.confirm(f"Overwrite {out}?", default=False):
            output.diagnostic(f"aborted; {out} left unchanged")
            return
    try:
        out.write_text(result + "\n", encoding="utf-8")
    except OSError as err:
        raise click.ClickException(str(err)) from err
    output.diagnostic(f"wrote {out}")


@text.command(help="Convert text to a lowercase hyphenated slug.")
@click.argument("words", nargs=-1, required=True)
@click.option("--out", type=click.Path(path_type=Path), help="Write to this file.")
@click.option("--force", is_flag=True, help="Overwrite the --out file if it exists.")
@global_options
@click.pass_context
def slugify(
    ctx: click.Context,
    words: tuple[str, ...],
    out: Path | None,
    force: bool,
    **kwargs,
) -> None:
    state = _resolve_state(_merge_globals(ctx, kwargs))
    result = textkit.slugify(" ".join(words))
    _deliver(state, result, None, out, force)


@text.command(help="Shorten text to at most --max characters.")
@click.option(
    "--max",
    "max_length",
    type=int,
    default=40,
    show_default=True,
    help="Maximum length in characters (including the ellipsis).",
)
@click.argument("words", nargs=-1, required=True)
@click.option("--out", type=click.Path(path_type=Path), help="Write to this file.")
@click.option("--force", is_flag=True, help="Overwrite the --out file if it exists.")
@global_options
@click.pass_context
def truncate(
    ctx: click.Context,
    max_length: int,
    words: tuple[str, ...],
    out: Path | None,
    force: bool,
    **kwargs,
) -> None:
    state = _resolve_state(_merge_globals(ctx, kwargs))
    if max_length < 1:
        raise click.UsageError(f"--max must be at least 1, got {max_length}")
    source = " ".join(words)
    result = textkit.truncate(source, max_length)
    _deliver(state, result, {"truncated": result != source}, out, force)


@cli.command(
    name="completions",
    hidden=True,
    help="Print a shell completion script (bash, zsh, fish), "
    "generated from the command tree itself.",
)
@click.argument("shell", type=click.Choice(["bash", "zsh", "fish"]))
def completions(shell: str) -> None:
    completion_class = get_completion_class(shell)
    if completion_class is None:  # pragma: no cover - guarded by Choice
        raise click.UsageError(f"unsupported shell: {shell}")
    completion = completion_class(cli, {}, "{{project-name}}", "_" + _env_prefix() + "COMPLETE")
    click.echo(completion.source())
