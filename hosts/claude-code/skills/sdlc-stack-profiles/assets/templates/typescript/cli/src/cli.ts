/**
 * The command tree over the textkit core.
 *
 * The command surface is a contract (see the cli standard in the
 * sdlc-stack-profiles skill): data goes to stdout, diagnostics to
 * stderr, and exit codes follow the documented map — 0 success,
 * 1 failure, 2 usage error. Commander reports every parse failure
 * as 1, so `run` catches its errors and maps them itself.
 *
 * Global options may be given at any level of the tree: every level
 * carries the same option definitions, and `optsWithGlobals` merges
 * them with the innermost explicit value winning per option.
 */

import fs from "node:fs";

import { Command, CommanderError, Option } from "commander";

import pkg from "../package.json" with { type: "json" };
import { Output, type Write } from "./output.js";
import * as textkit from "./textkit.js";

const LONG_HELP = `{{ProjectName}} is a sample command-line tool built from the typescript/cli
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
the environment, never from flags.`;

/** An expected, user-facing failure: message on stderr, exit 1. */
export class CliFailure extends Error {}

/** A usage-class failure raised after parsing (a bad option value): exit 2. */
export class CliUsage extends Error {}

export interface Io {
  stdout: Write;
  stderr: Write;
}

interface Globals {
  format: string;
  formatFromCli: boolean;
  json: boolean;
  noColor: boolean;
  verbose: boolean;
  quiet: boolean;
  noInput: boolean;
  dryRun: boolean;
}

function globalOptions(command: Command): Command {
  return command
    .addOption(
      new Option(
        "--format <format>",
        "Output format for data commands: plain or json.",
      ).default("plain"),
    )
    .option("--json", "Shorthand for --format json.")
    .option(
      "--no-color",
      "Disable colour in diagnostics (NO_COLOR is also honoured).",
    )
    .option("--verbose", "Print diagnostics about what the command is doing.")
    .option("--quiet", "Suppress diagnostics.")
    .option("--no-input", "Never prompt; fail instead of asking.")
    .option("--dry-run", "Show what would happen without writing anything.");
}

function readGlobals(command: Command): Globals {
  const opts = command.optsWithGlobals();
  return {
    format: String(opts.format ?? "plain"),
    formatFromCli: command.getOptionValueSourceWithGlobals("format") === "cli",
    json: Boolean(opts.json),
    noColor: Boolean(opts.noColor),
    verbose: Boolean(opts.verbose),
    quiet: Boolean(opts.quiet),
    noInput: Boolean(opts.noInput),
    dryRun: Boolean(opts.dryRun),
  };
}

function envPrefix(): string {
  return pkg.name.toUpperCase().replaceAll("-", "_") + "_";
}

interface State {
  output: Output;
  noInput: boolean;
  dryRun: boolean;
}

function resolveState(command: Command, io: Io): State {
  const globals = readGlobals(command);
  // Configuration precedence: an explicitly passed flag wins
  // (including the --json shorthand), then the environment, then
  // the default.
  let resolved: string;
  if (globals.json) {
    resolved = "json";
  } else if (globals.formatFromCli) {
    resolved = globals.format;
  } else {
    resolved = process.env[envPrefix() + "FORMAT"] ?? globals.format;
  }
  if (resolved !== "plain" && resolved !== "json") {
    throw new CliUsage(`invalid format '${resolved}': want plain or json`);
  }
  return {
    output: new Output(
      resolved,
      globals.noColor,
      globals.quiet,
      io.stdout,
      io.stderr,
    ),
    noInput: globals.noInput,
    dryRun: globals.dryRun,
  };
}

/** Route a verb's result: stdout by default, or a file with --out.
 * File delivery honours the safety contract — --dry-run writes
 * nothing, an existing file is never overwritten without --force,
 * and the user is only ever prompted at a terminal (and never with
 * --no-input). */
async function deliver(
  state: State,
  result: string,
  extra: Record<string, unknown> | undefined,
  out: string | undefined,
  force: boolean,
): Promise<void> {
  if (out === undefined) {
    state.output.result(result, extra);
    return;
  }
  if (state.dryRun) {
    state.output.diagnostic(
      `dry-run: would write ${result.length + 1} bytes to ${out}`,
    );
    return;
  }
  if (fs.existsSync(out) && !force) {
    if (state.noInput || !process.stdin.isTTY) {
      throw new CliFailure(`${out} already exists (use --force to overwrite)`);
    }
    const answer = await prompt(`Overwrite ${out}? [y/N] `);
    if (answer !== "y" && answer !== "Y") {
      state.output.diagnostic(`aborted; ${out} left unchanged`);
      return;
    }
  }
  try {
    fs.writeFileSync(out, result + "\n", "utf8");
  } catch (err) {
    throw new CliFailure(err instanceof Error ? err.message : String(err));
  }
  state.output.diagnostic(`wrote ${out}`);
}

function prompt(question: string): Promise<string> {
  return new Promise((resolve) => {
    process.stderr.write(question);
    process.stdin.once("data", (data) => resolve(data.toString().trim()));
  });
}

function buildSlugify(io: Io): Command {
  const command = new Command("slugify");
  command
    .description("Convert text to a lowercase hyphenated slug.")
    .argument("<text...>", "The text to slugify.")
    .option("--out <file>", "Write to this file.")
    .option("--force", "Overwrite the --out file if it exists.");
  globalOptions(command);
  command.action(
    async (words: string[], options: { out?: string; force?: boolean }) => {
      const state = resolveState(command, io);
      const result = textkit.slugify(words.join(" "));
      await deliver(
        state,
        result,
        undefined,
        options.out,
        Boolean(options.force),
      );
    },
  );
  return command;
}

function buildTruncate(io: Io): Command {
  const command = new Command("truncate");
  command
    .description("Shorten text to at most --max characters.")
    .option(
      "--max <n>",
      "Maximum length in characters (including the ellipsis).",
      "40",
    )
    .argument("<text...>", "The text to truncate.")
    .option("--out <file>", "Write to this file.")
    .option("--force", "Overwrite the --out file if it exists.");
  globalOptions(command);
  command.action(
    async (
      words: string[],
      options: { max: string; out?: string; force?: boolean },
    ) => {
      const state = resolveState(command, io);
      const max = Number(options.max);
      if (!Number.isInteger(max) || max < 1) {
        throw new CliUsage(
          `--max must be a positive integer, got '${options.max}'`,
        );
      }
      const source = words.join(" ");
      const result = textkit.truncate(source, max);
      await deliver(
        state,
        result,
        { truncated: result !== source },
        options.out,
        Boolean(options.force),
      );
    },
  );
  return command;
}

/** Build the root command writing to the given streams. */
export function buildProgram(io: Io): Command {
  const program = new Command(pkg.name);
  program
    .description(LONG_HELP)
    .version(`${pkg.name} ${pkg.version}`)
    .helpOption("-h, --help", "Show help and usage information.");
  globalOptions(program);

  const text = new Command("text");
  text.description("Text transformations over the textkit core.");
  globalOptions(text);
  text.addCommand(buildSlugify(io));
  text.addCommand(buildTruncate(io));
  program.addCommand(text);

  const completions = new Command("completions");
  completions
    .description(
      "Print a shell completion script, generated from the command tree itself.",
    )
    .argument("<shell>", "bash, zsh, or fish.")
    .action((shell: string) => {
      io.stdout(generateCompletions(program, shell) + "\n");
    });
  program.addCommand(completions, { hidden: true });

  // exitOverride + captured output on every level, so `run` owns
  // exit codes and tests own the streams.
  const walk = (command: Command): void => {
    command.exitOverride();
    command.configureOutput({
      writeOut: io.stdout,
      writeErr: io.stderr,
      outputError: (str, write) => write(str),
    });
    command.commands.forEach(walk);
  };
  walk(program);
  return program;
}

/** Generate a completion script from the live command tree: command
 * paths and their long flags. Deliberately small — word completion
 * for commands and options, nothing stateful. */
export function generateCompletions(program: Command, shell: string): string {
  const paths: string[] = [];
  const flagsByPath = new Map<string, string[]>();
  const walk = (command: Command, prefix: string): void => {
    const path = prefix === "" ? command.name() : `${prefix} ${command.name()}`;
    if (prefix !== "") {
      paths.push(path);
    }
    flagsByPath.set(
      path,
      command.options
        .map((option) => option.long)
        .filter((f): f is string => f !== undefined),
    );
    command.commands
      // Offer every visible command; the hidden `completions`
      // command itself is not part of the completed surface.
      .filter((sub) => sub.name() !== "completions")
      .forEach((sub) => walk(sub, path));
  };
  walk(program, "");
  const topLevel = program.commands.map((c) => c.name()).join(" ");
  const topFlags = (flagsByPath.get(program.name()) ?? []).join(" ");
  if (shell === "bash") {
    return [
      `# bash completion for ${program.name()} (generated by '${program.name()} completions bash')`,
      `_${program.name()}() {`,
      `  local cur prev`,
      `  cur="\${COMP_WORDS[COMP_CWORD]}"`,
      `  prev="\${COMP_WORDS[COMP_CWORD-1]}"`,
      `  if [ "$COMP_CWORD" -eq 1 ]; then`,
      `    COMPREPLY=( $(compgen -W "${topLevel} ${topFlags}" -- "$cur") )`,
      `  else`,
      `    COMPREPLY=( $(compgen -W "${paths.join(" ")}" -- "$cur") )`,
      `  fi`,
      `}`,
      `complete -F _${program.name()} ${program.name()}`,
    ].join("\n");
  }
  if (shell === "zsh" || shell === "fish") {
    const lines = paths.map(
      (p) => `# ${p}: ${(flagsByPath.get(p) ?? []).join(" ")}`,
    );
    return [
      `# ${shell} word list for ${program.name()} (generated by '${program.name()} completions ${shell}')`,
      `# commands: ${topLevel}`,
      ...lines,
    ].join("\n");
  }
  throw new CliUsage(`unsupported shell: ${shell}`);
}

/** Run the CLI over the given streams; returns the process exit code. */
export async function run(args: string[], io: Io): Promise<number> {
  const program = buildProgram(io);
  try {
    await program.parseAsync(args, { from: "user" });
    return 0;
  } catch (err) {
    if (err instanceof CommanderError) {
      // Help and version displays exit 0; every other commander
      // error is a usage failure — commander already wrote the
      // message to stderr.
      return err.exitCode === 0 ? 0 : 2;
    }
    if (err instanceof CliUsage) {
      io.stderr(`error: ${err.message}\n`);
      return 2;
    }
    if (err instanceof CliFailure) {
      io.stderr(`error: ${err.message}\n`);
      return 1;
    }
    io.stderr(`error: ${err instanceof Error ? err.message : String(err)}\n`);
    return 1;
  }
}
