/**
 * Contract tests for the CLI surface: golden files pin the help
 * and primary outputs, and exit-code tests pin the documented map
 * (0 success, 1 failure, 2 usage error). Regenerate goldens
 * deliberately with UPDATE_GOLDEN=1 pnpm test and review the diff
 * like an API change.
 */

import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { describe, expect, it } from "vitest";

import { run } from "../src/cli.js";

const TESTDATA = path.join(
  path.dirname(fileURLToPath(import.meta.url)),
  "testdata",
);

interface Captured {
  code: number;
  stdout: string;
  stderr: string;
}

async function runCli(
  args: string[],
  env: Record<string, string> = {},
): Promise<Captured> {
  let stdout = "";
  let stderr = "";
  const saved = { ...process.env };
  Object.assign(process.env, env);
  try {
    const code = await run(args, {
      stdout: (chunk) => {
        stdout += chunk;
      },
      stderr: (chunk) => {
        stderr += chunk;
      },
    });
    return { code, stdout, stderr };
  } finally {
    process.env = saved;
  }
}

function golden(name: string, actual: string): void {
  const file = path.join(TESTDATA, `${name}.golden`);
  if (process.env.UPDATE_GOLDEN === "1") {
    fs.writeFileSync(file, actual, "utf8");
    return;
  }
  expect(actual).toBe(fs.readFileSync(file, "utf8"));
}

describe("golden outputs", () => {
  const cases: Array<[string, string[]]> = [
    ["help-root", ["--help"]],
    ["help-text", ["text", "--help"]],
    ["slugify", ["text", "slugify", "Hello, World!"]],
    ["slugify-json", ["text", "slugify", "--json", "Hello, World!"]],
    ["truncate", ["text", "truncate", "--max", "6", "a longer sentence"]],
    [
      "truncate-json",
      ["text", "truncate", "--max", "6", "--json", "a longer sentence"],
    ],
    ["version", ["--version"]],
  ];
  for (const [name, args] of cases) {
    it(name, async () => {
      const { code, stdout } = await runCli(args);
      expect(code).toBe(0);
      golden(name, stdout);
    });
  }
});

describe("exit codes", () => {
  const cases: Array<[string[], number]> = [
    [["text", "slugify", "Hello"], 0],
    [["frobnicate"], 2],
    [["text", "slugify"], 2],
    [["text", "truncate", "--max", "abc", "text"], 2],
    [["text", "truncate", "--max", "0", "text"], 2],
    [["--format", "yaml", "text", "slugify", "Hi"], 2],
    [["text", "slugify", "--out", "/nonexistent-dir/x.txt", "Hi"], 1],
  ];
  for (const [args, want] of cases) {
    it(`${args.join(" ")} -> ${want}`, async () => {
      const { code } = await runCli(args);
      expect(code).toBe(want);
    });
  }
});

describe("format precedence", () => {
  it("flags beat the environment, the environment beats the default", async () => {
    const fromEnv = await runCli(["text", "slugify", "Hi There"], {
      SAMPLE_FORMAT: "json",
    });
    expect(fromEnv.stdout.startsWith("{")).toBe(true);

    const fromFlag = await runCli(
      ["--format", "plain", "text", "slugify", "Hi There"],
      {
        SAMPLE_FORMAT: "json",
      },
    );
    expect(fromFlag.stdout).toBe("hi-there\n");
  });
});

describe("file delivery", () => {
  it("dry-run writes nothing; overwrite needs --force", async () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), "{{project-name}}-cli-test-"));
    try {
      const target = path.join(dir, "out.txt");

      let result = await runCli([
        "text",
        "slugify",
        "--dry-run",
        "--out",
        target,
        "Hello World",
      ]);
      expect(result.code).toBe(0);
      expect(fs.existsSync(target)).toBe(false);

      result = await runCli([
        "text",
        "slugify",
        "--out",
        target,
        "Hello World",
      ]);
      expect(result.code).toBe(0);
      expect(fs.readFileSync(target, "utf8")).toBe("hello-world\n");

      result = await runCli([
        "text",
        "slugify",
        "--out",
        target,
        "Changed Text",
      ]);
      expect(result.code).toBe(1);
      expect(fs.readFileSync(target, "utf8")).toBe("hello-world\n");

      result = await runCli([
        "text",
        "slugify",
        "--out",
        target,
        "--force",
        "Changed Text",
      ]);
      expect(result.code).toBe(0);
      expect(fs.readFileSync(target, "utf8")).toBe("changed-text\n");
    } finally {
      fs.rmSync(dir, { recursive: true, force: true });
    }
  });
});

describe("completions", () => {
  it("generates a bash script from the command tree", async () => {
    const { code, stdout } = await runCli(["completions", "bash"]);
    expect(code).toBe(0);
    expect(stdout).toContain("slugify");
    expect(stdout).toContain("--format");
  });
});
