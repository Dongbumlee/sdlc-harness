package com.example.{{PackageName}}.cli;

import java.io.PrintWriter;
import picocli.CommandLine.Model.CommandSpec;
import picocli.CommandLine.Option;
import picocli.CommandLine.ScopeType;
import picocli.CommandLine.Spec;

/**
 * The global options, declared once with INHERIT scope so picocli accepts them at any level of the
 * tree ({@code tool --json text slugify}, {@code tool text --json slugify}, and {@code tool text
 * slugify --json} are equivalent) and every command reads the same values.
 */
final class Globals {

  @Spec CommandSpec spec;

  @Option(
      names = "--format",
      description = "Output format for data commands: plain or json.",
      scope = ScopeType.INHERIT,
      defaultValue = "plain")
  String format;

  @Option(names = "--json", description = "Shorthand for --format json.", scope = ScopeType.INHERIT)
  boolean json;

  @Option(
      names = "--no-color",
      description = "Disable colour in diagnostics (NO_COLOR is also honoured).",
      scope = ScopeType.INHERIT)
  boolean noColor;

  @Option(
      names = "--verbose",
      description = "Print diagnostics about what the command is doing.",
      scope = ScopeType.INHERIT)
  boolean verbose;

  @Option(names = "--quiet", description = "Suppress diagnostics.", scope = ScopeType.INHERIT)
  boolean quiet;

  @Option(
      names = "--no-input",
      description = "Never prompt; fail instead of asking.",
      scope = ScopeType.INHERIT)
  boolean noInput;

  @Option(
      names = "--dry-run",
      description = "Show what would happen without writing anything.",
      scope = ScopeType.INHERIT)
  boolean dryRun;

  /** The resolved settings for one leaf invocation. */
  record State(Output output, boolean noInput, boolean dryRun) {}

  /**
   * Apply configuration precedence and build the leaf state: an explicitly passed flag wins
   * (including the --json shorthand), then the environment, then the default.
   */
  State resolve(PrintWriter stdout, PrintWriter stderr) {
    String resolved;
    if (json) {
      resolved = "json";
    } else if (spec.commandLine().getParseResult().hasMatchedOption("--format")) {
      resolved = format;
    } else {
      var fromEnv = System.getenv(envPrefix() + "FORMAT");
      resolved = fromEnv != null ? fromEnv : format;
    }
    if (!resolved.equals("plain") && !resolved.equals("json")) {
      throw new CliUsageException("invalid format '" + resolved + "': want plain or json");
    }
    return new State(new Output(stdout, stderr, resolved, noColor, quiet), noInput, dryRun);
  }

  static String envPrefix() {
    return "{{project-name}}".toUpperCase().replace('-', '_') + "_";
  }
}
