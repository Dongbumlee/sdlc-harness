#!/usr/bin/env node
/** Thin entry point: everything testable lives in `cli`, and the
 * process exit code is the CLI contract's map, computed there.
 * (No top-level await: the release pipeline bundles this file to
 * CommonJS for the Node SEA binary, which cannot express it.) */
import { run } from "./cli.js";

const io = {
  stdout: (chunk: string) => {
    process.stdout.write(chunk);
  },
  stderr: (chunk: string) => {
    process.stderr.write(chunk);
  },
};

void (async () => {
  process.exitCode = await run(process.argv.slice(2), io);
})();
