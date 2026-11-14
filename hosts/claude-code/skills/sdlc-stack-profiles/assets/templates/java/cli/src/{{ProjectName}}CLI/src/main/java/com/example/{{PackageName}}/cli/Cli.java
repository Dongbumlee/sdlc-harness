package com.example.{{PackageName}}.cli;

import java.io.InputStream;
import java.util.Properties;
import java.util.concurrent.Callable;
import picocli.CommandLine.Command;
import picocli.CommandLine.IVersionProvider;
import picocli.CommandLine.Mixin;
import picocli.CommandLine.Model.CommandSpec;
import picocli.CommandLine.Spec;

/**
 * The command tree over the textkit core. The command surface is a contract (see the cli standard
 * in the sdlc-stack-profiles skill): data goes to stdout, diagnostics to stderr, and exit codes
 * follow the documented map — 0 success, 1 failure, 2 usage error (picocli's defaults already are
 * the map; Main's handler covers failures raised after parsing).
 */
@Command(
    name = "{{project-name}}",
    subcommands = {TextCommands.class, CompletionsCommand.class},
    mixinStandardHelpOptions = true,
    versionProvider = Cli.VersionProvider.class,
    description = {
      "{{ProjectName}} is a sample command-line tool built from the java/cli",
      "template. It demonstrates the CLI contract: data goes to stdout,",
      "diagnostics go to stderr, and the command surface (flags, output",
      "schema, exit codes) is a tested API.",
      "",
      "Exit codes:",
      "  0  success",
      "  1  failure (the command ran but could not complete)",
      "  2  usage error (unknown command, bad flags, invalid arguments)",
      "",
      "Configuration precedence: flags, then environment",
      "(<PREFIX>_FORMAT and friends, where the prefix is the",
      "upper-cased tool name), then defaults. Secrets are read from",
      "the environment, never from flags."
    })
public final class Cli implements Callable<Integer> {

  @Mixin Globals globals;

  @Spec CommandSpec spec;

  @Override
  public Integer call() {
    // A bare invocation shows the help and succeeds.
    spec.commandLine().usage(spec.commandLine().getOut());
    return 0;
  }

  /**
   * The version comes from version.properties, which Maven filters from the pom at build time — so
   * --version reports the same version in tests, in the jar, and in the packaged app image.
   */
  static final class VersionProvider implements IVersionProvider {
    @Override
    public String[] getVersion() throws Exception {
      var props = new Properties();
      try (InputStream in = Cli.class.getResourceAsStream("/version.properties")) {
        if (in != null) {
          props.load(in);
        }
      }
      return new String[] {"{{project-name}} " + props.getProperty("version", "dev")};
    }
  }
}
