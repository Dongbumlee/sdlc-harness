import { describe, expect, it } from "vitest";

import { ItemsService } from "./ItemsService";

describe("ItemsService", () => {
  it("creates and retrieves an item", () => {
    const service = new ItemsService();
    const item = service.create("first", "sample");
    expect(item.id).toBeGreaterThan(0);
    expect(service.get(item.id)?.name).toBe("first");
  });

  it("lists created items", () => {
    const service = new ItemsService();
    service.create("listed");
    expect(service.list().map((item) => item.name)).toContain("listed");
  });

  it("rejects an empty name", () => {
    const service = new ItemsService();
    expect(() => service.create("")).toThrowError("Name is required.");
  });
});
