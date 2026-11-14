package com.example.{{PackageName}}.cli;

import java.io.PrintWriter;
import java.util.Map;

/**
 * The stream contract: results on stdout (plain or JSON), diagnostics on stderr, and colour only
 * where a human is looking at a terminal — never in piped data.
 */
final class Output {

  private final PrintWriter stdout;
  private final PrintWriter stderr;
  private final String format;
  private final boolean color;
  private final boolean quiet;

  Output(PrintWriter stdout, PrintWriter stderr, String format, boolean noColor, boolean quiet) {
    this.stdout = stdout;
    this.stderr = stderr;
    this.format = format;
    this.color = colorEnabled(noColor);
    this.quiet = quiet;
  }

  /**
   * Print a command's primary data to stdout. In JSON mode the value is wrapped in an object with a
   * stable {@code result} field; callers may add fields but the shape never changes within a major
   * version.
   */
  void result(String value, Map<String, Object> extra) {
    if (format.equals("json")) {
      var json = new StringBuilder("{\"result\":\"").append(escapeJson(value)).append('"');
      extra.forEach(
          (key, fieldValue) ->
              json.append(",\"").append(key).append("\":").append(jsonValue(fieldValue)));
      stdout.println(json.append('}'));
    } else {
      stdout.println(value);
    }
  }

  /** Print a human-only note to stderr, unless --quiet. Diagnostics never carry primary data. */
  void diagnostic(String message) {
    if (quiet) {
      return;
    }
    stderr.println(color ? "\u001b[2m" + message + "\u001b[0m" : message);
  }

  private static String escapeJson(String value) {
    return value.replace("\\", "\\\\").replace("\"", "\\\"");
  }

  private static String jsonValue(Object value) {
    return value instanceof Boolean bool
        ? bool.toString()
        : "\"" + escapeJson(value.toString()) + "\"";
  }

  /**
   * Decide whether styled diagnostics are appropriate: an explicit --no-color or the NO_COLOR
   * environment variable wins, and colour is only ever used on a terminal.
   */
  private static boolean colorEnabled(boolean noColorFlag) {
    if (noColorFlag) {
      return false;
    }
    if (System.getenv("NO_COLOR") != null) {
      return false;
    }
    return System.console() != null;
  }
}
