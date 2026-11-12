package com.example.{{PackageName}}.cli;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.io.IOException;
import java.io.PrintWriter;
import java.io.StringWriter;
import java.nio.file.Files;
import java.nio.file.Path;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;

/**
 * Contract tests for the CLI surface: golden files pin the help and primary outputs, and exit code
 * tests pin the documented map (0 success, 1 failure, 2 usage error). Regenerate goldens
 * deliberately by running the tests once with -Dupdate.golden=true and review the diff like an API
 * change. Environment precedence is covered at the packaged-jar level in CI: the JVM cannot set its
 * own environment portably, and faking it would test the fake.
 */
class CliContractTest {

  record Run(int code, String stdout, String stderr) {}

  static Run run(String... args) {
    var out = new StringWriter();
    var err = new StringWriter();
    var cmd = CliApp.create();
    cmd.setOut(new PrintWriter(out, true));
    cmd.setErr(new PrintWriter(err, true));
    int code = cmd.execute(args);
    return new Run(code, out.toString(), err.toString());
  }

  static void golden(String name, String actual) throws IOException {
    var file = Path.of("src/test/resources/testdata", name + ".golden");
    if (Boolean.getBoolean("update.golden")) {
      Files.createDirectories(file.getParent());
      Files.writeString(file, actual);
      return;
    }
    assertEquals(Files.readString(file), actual, "golden mismatch for " + name);
  }

  @ParameterizedTest(name = "{0}")
  @CsvSource({
    "help-root, --help",
    "help-text, text --help",
    "slugify, text slugify Hello World!",
    "slugify-json, text slugify --json Hello World!",
    "truncate, text truncate --max 6 a longer sentence",
    "truncate-json, text truncate --max 6 --json a longer sentence",
    "version, --version",
  })
  void goldenOutputs(String name, String commandLine) throws IOException {
    var args = commandLine.trim().split("\\s+");
    var run = run(args);
    assertEquals(0, run.code(), name + " stderr: " + run.stderr());
    golden(name, run.stdout());
  }

  @ParameterizedTest(name = "{0} -> {1}")
  @CsvSource({
    "'text slugify Hello', 0",
    "'frobnicate', 2",
    "'text slugify', 2",
    "'text truncate --max abc text', 2",
    "'text truncate --max 0 text', 2",
    "'--format yaml text slugify Hi', 2",
    "'text slugify --out /nonexistent-dir/x.txt Hi', 1",
  })
  void exitCodes(String commandLine, int want) {
    var run = run(commandLine.trim().split("\\s+"));
    assertEquals(want, run.code(), "stderr: " + run.stderr());
  }

  @Test
  void globalOptionsWorkAtAnyLevel() {
    var atLeaf = run("text", "slugify", "--json", "Hi There");
    assertTrue(atLeaf.stdout().startsWith("{"), atLeaf.stdout());
    var atRoot = run("--json", "text", "slugify", "Hi There");
    assertEquals(atLeaf.stdout(), atRoot.stdout());
  }

  @Test
  void jsonShorthandAndExplicitFormatPrecedence() {
    var shorthand = run("text", "slugify", "--json", "Hi There");
    assertTrue(shorthand.stdout().startsWith("{"));
    var explicit = run("--format", "plain", "text", "slugify", "Hi There");
    assertEquals("hi-there" + System.lineSeparator(), explicit.stdout());
  }

  @Test
  void fileDeliveryDryRunForce(@TempDir Path dir) throws IOException {
    var target = dir.resolve("out.txt");

    var dry = run("text", "slugify", "--dry-run", "--out", target.toString(), "Hello World");
    assertEquals(0, dry.code());
    assertFalse(Files.exists(target));

    var write = run("text", "slugify", "--out", target.toString(), "Hello World");
    assertEquals(0, write.code());
    assertEquals("hello-world" + System.lineSeparator(), Files.readString(target));

    var refuse = run("text", "slugify", "--out", target.toString(), "Changed Text");
    assertEquals(1, refuse.code());
    assertEquals("hello-world" + System.lineSeparator(), Files.readString(target));

    var forced = run("text", "slugify", "--out", target.toString(), "--force", "Changed Text");
    assertEquals(0, forced.code());
    assertEquals("changed-text" + System.lineSeparator(), Files.readString(target));
  }

  @Test
  void completionsGenerateFromTheModel() {
    var run = run("completions", "bash");
    assertEquals(0, run.code());
    assertTrue(run.stdout().contains("slugify"), run.stdout().substring(0, 200));
    assertTrue(run.stdout().contains("--format"));
    assertEquals(2, run("completions", "fish").code());
  }

  @Test
  void versionMatchesPomVersion() throws IOException {
    var run = run("--version");
    assertEquals(0, run.code());
    assertTrue(run.stdout().startsWith("{{project-name}} 0.1.0"), run.stdout());
  }
}
