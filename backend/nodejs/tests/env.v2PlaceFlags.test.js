import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

describe("v2 place feature flags", () => {
  beforeEach(() => {
    vi.resetModules();
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  it("USE_V2_PLACE_TABLES=true forces PLACE_ID_LEGACY_FALLBACK=false", async () => {
    vi.stubEnv("USE_V2_PLACE_TABLES", "true");
    vi.stubEnv("PLACE_ID_LEGACY_FALLBACK", "true");
    const env = await import("../src/config/env.js");
    expect(env.USE_V2_PLACE_TABLES).toBe(true);
    expect(env.PLACE_ID_LEGACY_FALLBACK).toBe(false);
  });

  it("legacy fallback defaults true when v2 flag off", async () => {
    vi.stubEnv("USE_V2_PLACE_TABLES", "false");
    delete process.env.PLACE_ID_LEGACY_FALLBACK;
    const env = await import("../src/config/env.js");
    expect(env.USE_V2_PLACE_TABLES).toBe(false);
    expect(env.PLACE_ID_LEGACY_FALLBACK).toBe(true);
  });
});
