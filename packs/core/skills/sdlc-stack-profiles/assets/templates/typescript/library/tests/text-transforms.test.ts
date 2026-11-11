import { describe, expect, it } from "vitest";

import * as api from "../src/index.js";
import { slugify, truncate } from "../src/index.js";

// Black-box tests: they use only the public entry point, exactly
// like a consumer. Nothing here reaches into implementation files.
describe("slugify", () => {
  it("lowercases and hyphenates words", () => {
    expect(slugify("Hello, World!")).toBe("hello-world");
  });

  it("folds accents to ASCII base letters", () => {
    expect(slugify("Crème brûlée")).toBe("creme-brulee");
  });

  it("collapses separator runs and trims hyphens", () => {
    expect(slugify("  --Already--Slugged--  ")).toBe("already-slugged");
  });

  it("returns an empty slug for empty input", () => {
    expect(slugify("   ")).toBe("");
  });
});

describe("truncate", () => {
  it("returns text that fits unchanged", () => {
    expect(truncate("short", 10)).toBe("short");
  });

  it("cuts to the limit including the ellipsis", () => {
    expect(truncate("hello world", 8)).toBe("hello w…");
  });

  it("rejects a negative limit", () => {
    expect(() => truncate("abc", -1)).toThrow(RangeError);
  });
});

describe("public surface", () => {
  it("exports exactly the declared API", () => {
    expect(Object.keys(api).sort()).toEqual(["slugify", "truncate"]);
  });
});
