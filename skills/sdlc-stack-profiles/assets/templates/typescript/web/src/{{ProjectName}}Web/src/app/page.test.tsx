import { readFileSync } from "node:fs";
import path from "node:path";

import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import RootLayout from "./layout";
import HomePage from "./page";

// The web type's markup floor, asserted on the composed page the
// way a browser receives it: a skip link, landmark regions,
// exactly one h1, and a labelled form control — so a new page
// cannot silently drop the floor. The document's language
// attribute is asserted on the layout source: React renders the
// <html> element as the document itself, so it never appears
// inside a test container.

describe("markup floor", () => {
  it("sets the document language in the root layout", () => {
    const layout = readFileSync(path.join(__dirname, "layout.tsx"), "utf8");
    expect(layout).toContain('<html lang="en">');
  });

  it("holds on the home page", () => {
    render(
      <RootLayout>
        <HomePage />
      </RootLayout>,
    );
    expect(screen.getByText("Skip to main content")).toBeTruthy();
    expect(screen.getByRole("banner")).toBeTruthy();
    expect(screen.getByRole("navigation", { name: "Primary" })).toBeTruthy();
    expect(screen.getByRole("main")).toBeTruthy();
    expect(screen.getByRole("contentinfo")).toBeTruthy();
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
    expect(screen.getByLabelText("Item name")).toBeTruthy();
  });
});
