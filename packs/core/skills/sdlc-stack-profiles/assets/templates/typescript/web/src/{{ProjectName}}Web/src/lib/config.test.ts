import { afterEach, describe, expect, it, vi } from "vitest";

// Configuration modules read the environment at import time, so
// each case stubs the env first and imports a fresh module.

afterEach(() => {
  vi.unstubAllEnvs();
  vi.resetModules();
});

describe("publicConfig", () => {
  it("defaults the app name to the product name", async () => {
    const { publicConfig } = await import("./config");
    expect(publicConfig.appName).toBe("{{ProjectName}}");
  });

  it("reads the NEXT_PUBLIC_ override", async () => {
    vi.stubEnv("NEXT_PUBLIC_APP_NAME", "Public Name");
    const { publicConfig } = await import("./config");
    expect(publicConfig.appName).toBe("Public Name");
  });
});

describe("serverConfig", () => {
  it("defaults the api key to empty", async () => {
    const { serverConfig } = await import("./server-config");
    expect(serverConfig.apiKey).toBe("");
  });

  it("reads the unprefixed server variable", async () => {
    vi.stubEnv("SERVER_API_KEY", "sentinel-secret-12345");
    const { serverConfig } = await import("./server-config");
    expect(serverConfig.apiKey).toBe("sentinel-secret-12345");
  });

  it("never surfaces the server key through the public config", async () => {
    vi.stubEnv("SERVER_API_KEY", "sentinel-secret-12345");
    const { publicConfig } = await import("./config");
    expect(JSON.stringify(publicConfig)).not.toContain("sentinel-secret-12345");
  });
});
