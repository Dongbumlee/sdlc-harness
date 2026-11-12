package com.example.{{PackageName}}.cli;

import com.example.{{PackageName}}.textkit.TextKit;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.concurrent.Callable;
import picocli.CommandLine.Command;
import picocli.CommandLine.Model.CommandSpec;
import picocli.CommandLine.Option;
import picocli.CommandLine.Parameters;
import picocli.CommandLine.ParentCommand;
import picocli.CommandLine.Spec;

/**
 * The sample {@code text} noun: its verbs run over the textkit core. The global options are
 * declared once on the root command (Globals, INHERIT scope); the leaves read them through the
 * parent chain.
 */
@Command(
    name = "text",
    mixinStandardHelpOptions = true,
    subcommands = {TextCommands.Slugify.class, TextCommands.Truncate.class},
    description = "Text transformations over the library core.")
public final class TextCommands implements Callable<Integer> {

  @ParentCommand Cli root;

  @Spec CommandSpec spec;

  @Override
  public Integer call() {
    // A bare group invocation shows the group's help.
    spec.commandLine().usage(spec.commandLine().getOut());
    return 0;
  }

  /** Slugify free text: lowercase, letters and digits kept, other runs become single hyphens. */
  @Command(name = "slugify", mixinStandardHelpOptions = true, description = "Slugify text.")
  static final class Slugify implements Callable<Integer> {

    @ParentCommand TextCommands group;

    @Spec CommandSpec spec;

    @Parameters(arity = "1..*", paramLabel = "<text>", description = "The text to slugify.")
    List<String> text;

    @Option(names = "--out", description = "Write the result to this file instead of stdout.")
    Path out;

    @Option(
        names = "--force",
        description = "Overwrite the --out file if it exists (required for non-interactive runs).")
    boolean force;

    @Override
    public Integer call() {
      var state =
          group.root.globals.resolve(spec.commandLine().getOut(), spec.commandLine().getErr());
      var result = TextKit.slugify(String.join(" ", text));
      Delivery.deliver(state, result, out, force);
      return 0;
    }
  }

  /** Truncate text to a maximum length, marking the cut with an ellipsis. */
  @Command(name = "truncate", mixinStandardHelpOptions = true, description = "Truncate text.")
  static final class Truncate implements Callable<Integer> {

    @ParentCommand TextCommands group;

    @Spec CommandSpec spec;

    @Parameters(arity = "1..*", paramLabel = "<text>", description = "The text to truncate.")
    List<String> text;

    @Option(names = "--max", description = "Maximum length of the result.", defaultValue = "40")
    int max;

    @Option(names = "--out", description = "Write the result to this file instead of stdout.")
    Path out;

    @Option(
        names = "--force",
        description = "Overwrite the --out file if it exists (required for non-interactive runs).")
    boolean force;

    @Override
    public Integer call() {
      if (max < 1) {
        throw new CliUsageException("--max must be at least 1");
      }
      var state =
          group.root.globals.resolve(spec.commandLine().getOut(), spec.commandLine().getErr());
      var source = String.join(" ", text);
      var result = TextKit.truncate(source, max);
      Delivery.deliver(state, result, out, force, Map.of("truncated", !result.equals(source)));
      return 0;
    }
  }
}

/** Shared --out delivery: no accidental overwrites, nothing written on --dry-run. */
final class Delivery {

  private Delivery() {}

  static void deliver(Globals.State state, String result, Path out, boolean force) {
    deliver(state, result, out, force, Map.of());
  }

  static void deliver(
      Globals.State state, String result, Path out, boolean force, Map<String, Object> extra) {
    var output = state.output();
    if (out == null) {
      output.result(result, extra);
      return;
    }
    if (state.dryRun()) {
      output.diagnostic("dry run: would write '" + result + "' to " + out);
      return;
    }
    if (Files.exists(out) && !force) {
      if (!state.noInput() && System.console() != null) {
        var answer = System.console().readLine("%s exists. Overwrite? [y/N] ", out);
        if (!"y".equalsIgnoreCase(answer == null ? "" : answer.trim())) {
          throw new CliFailureException("not overwriting " + out);
        }
      } else {
        throw new CliFailureException(out + " exists (pass --force to overwrite it)");
      }
    }
    try {
      Files.writeString(out, result + System.lineSeparator(), StandardCharsets.UTF_8);
    } catch (IOException e) {
      throw new CliFailureException("cannot write " + out + ": " + e.getMessage());
    }
    output.diagnostic("wrote " + out);
  }
}
