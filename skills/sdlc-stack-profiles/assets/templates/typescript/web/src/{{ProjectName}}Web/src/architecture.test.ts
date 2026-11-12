import { readdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";

// Architecture conformance: the template's dependency direction is
// enforced mechanically, not left to review. app -> Components ->
// Services / lib. Components/ui and lib are leaves: they import no other
// layer. A violation fails the test run instead of waiting for a
// reviewer to notice it.

const SRC = path.resolve(__dirname);

type Layer = "app" | "Components" | "ui" | "Services" | "lib" | "other";

function classify(rel: string): Layer {
  if (rel.startsWith("app/")) return "app";
  if (rel.startsWith("Components/ui/")) return "ui";
  if (rel.startsWith("Components/")) return "Components";
  if (rel.startsWith("Services/")) return "Services";
  if (rel.startsWith("lib/")) return "lib";
  return "other";
}

function layerOfFile(file: string): Layer {
  return classify(path.relative(SRC, file).split(path.sep).join("/"));
}

function layerOfImport(spec: string, fromFile: string): Layer | null {
  let rel: string | null = null;
  if (spec.startsWith("@/")) {
    rel = spec.slice(2);
  } else if (spec.startsWith(".")) {
    rel = path
      .relative(SRC, path.resolve(path.dirname(fromFile), spec))
      .split(path.sep)
      .join("/");
  }
  return rel === null ? null : classify(rel);
}

const FORBIDDEN: Record<string, ReadonlySet<Layer>> = {
  Services: new Set<Layer>(["app", "Components", "ui"]),
  ui: new Set<Layer>(["app", "Components", "Services"]),
  lib: new Set<Layer>(["app", "Components", "ui", "Services"]),
  Components: new Set<Layer>(["app"]),
};

function* walk(dir: string): Generator<string> {
  for (const entry of readdirSync(dir)) {
    const full = path.join(dir, entry);
    if (statSync(full).isDirectory()) {
      yield* walk(full);
    } else if (/\.tsx?$/.test(entry) && !/\.test\.tsx?$/.test(entry)) {
      yield full;
    }
  }
}

describe("architecture", () => {
  it("keeps server-only configuration out of client code", () => {
    // The web type's structural env split: lib/server-config holds
    // secrets with no NEXT_PUBLIC_ prefix. Only server-side code
    // (app-layer files without "use client") may import it — a
    // client component importing it would ship the values to the
    // browser the moment anything re-exports them.
    const violations: string[] = [];
    for (const file of walk(SRC)) {
      const layer = layerOfFile(file);
      const text = readFileSync(file, "utf8");
      const isClient = /["']use client["']/.test(text);
      for (const match of text.matchAll(/from\s+["']([^"']+)["']/g)) {
        if (!match[1].endsWith("server-config")) continue;
        if (layer !== "app" || isClient) {
          violations.push(
            `${path.relative(SRC, file)} (${layer}${isClient ? ", client" : ""}) imports ${match[1]}`,
          );
        }
      }
    }
    expect(violations).toEqual([]);
  });

  it("respects layer dependency direction", () => {
    const violations: string[] = [];
    for (const file of walk(SRC)) {
      const src = layerOfFile(file);
      const banned = FORBIDDEN[src];
      if (!banned) continue;
      const text = readFileSync(file, "utf8");
      for (const match of text.matchAll(/from\s+["']([^"']+)["']/g)) {
        const dst = layerOfImport(match[1], file);
        if (dst !== null && banned.has(dst)) {
          violations.push(
            `${path.relative(SRC, file)} (${src}) imports ${match[1]} (${dst})`,
          );
        }
      }
    }
    expect(violations).toEqual([]);
  });
});
