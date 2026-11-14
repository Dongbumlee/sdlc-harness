/**
 * The stream contract: results on stdout (plain or JSON),
 * diagnostics on stderr, and colour only where a human is looking
 * at a terminal — never in piped data.
 */

export type Write = (chunk: string) => void;

export class Output {
  readonly #format: string;
  readonly #color: boolean;
  readonly #quiet: boolean;
  readonly #stdout: Write;
  readonly #stderr: Write;

  constructor(
    format: string,
    noColor: boolean,
    quiet: boolean,
    stdout: Write,
    stderr: Write,
  ) {
    this.#format = format;
    this.#color = colorEnabled(noColor);
    this.#quiet = quiet;
    this.#stdout = stdout;
    this.#stderr = stderr;
  }

  /** Print a command's primary data to stdout. In JSON mode the
   * value is wrapped in an object with a stable `result` field;
   * callers may add fields but the shape never changes within a
   * major version. */
  result(value: string, extra?: Record<string, unknown>): void {
    if (this.#format === "json") {
      this.#stdout(JSON.stringify({ result: value, ...extra }) + "\n");
    } else {
      this.#stdout(value + "\n");
    }
  }

  /** Print a human-only note to stderr, unless --quiet.
   * Diagnostics never carry primary data. */
  diagnostic(message: string): void {
    if (this.#quiet) {
      return;
    }
    this.#stderr(this.#color ? `\x1b[2m${message}\x1b[0m\n` : message + "\n");
  }
}

/** Decide whether styled diagnostics are appropriate: an explicit
 * --no-color or the NO_COLOR environment variable wins, and colour
 * is only ever used on a terminal. */
export function colorEnabled(noColorFlag: boolean): boolean {
  if (noColorFlag) {
    return false;
  }
  if (process.env.NO_COLOR !== undefined) {
    return false;
  }
  return process.stderr.isTTY === true;
}
