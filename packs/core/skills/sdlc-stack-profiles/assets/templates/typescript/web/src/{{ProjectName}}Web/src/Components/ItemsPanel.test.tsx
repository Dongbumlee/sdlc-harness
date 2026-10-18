import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { ItemsPanel } from "./ItemsPanel";

describe("ItemsPanel", () => {
  it("renders the project heading and add control", () => {
    render(<ItemsPanel />);
    expect(screen.getByRole("heading", { name: "{{ProjectName}}" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Add item" })).toBeTruthy();
    expect(screen.getByLabelText("Item name")).toBeTruthy();
  });
});
