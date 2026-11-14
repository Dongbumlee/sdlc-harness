package com.example.{{PackageName}}.cli;

import picocli.CommandLine;

/**
 * Builds the configured command line. Main and the contract tests share this factory so the tested
 * wiring is the shipped wiring (exit-code handler included).
 */
final class CliApp {

  private CliApp() {}

  static CommandLine create() {
    var cmd = new CommandLine(new Cli());
    // Failures raised after parsing: CliUsageException maps to 2, any other
    // expected failure to 1; the handler prints just the message, no stack trace.
    // (Parse failures are picocli's own and already exit 2 natively.)
    cmd.setExecutionExceptionHandler(
        (ex, commandLine, parseResult) -> {
          commandLine.getErr().println("error: " + ex.getMessage());
          return ex instanceof CliUsageException
              ? CommandLine.ExitCode.USAGE
              : CommandLine.ExitCode.SOFTWARE;
        });
    return cmd;
  }
}
