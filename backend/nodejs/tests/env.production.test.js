import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";

vi.mock("dotenv", () => ({
  default: { config: vi.fn(() => ({ parsed: {} })) }
}));

describe("assertSafeProductionConfig", () => {
  const envBackup = { ...process.env };

  beforeEach(() => {
    vi.resetModules();
    process.env = { ...envBackup };
  });

  afterEach(() => {
    process.env = { ...envBackup };
  });

  it("allows development without RAG keys", async () => {
    process.env.NODE_ENV = "development";
    delete process.env.RAG_INTERNAL_API_KEY;
    const { assertSafeProductionConfig } = await import("../src/config/env.js");
    expect(() => assertSafeProductionConfig()).not.toThrow();
  });

  it("throws in production when JWT_SECRET is default", async () => {
    process.env.NODE_ENV = "production";
    process.env.JWT_SECRET = "unutrip_dev_secret_change_me";
    process.env.RAG_INTERNAL_API_KEY = "internal-key-32-chars-minimum!!";
    process.env.RAG_ADMIN_API_KEY = "admin-key-32-chars-minimum!!!!!";
    const { assertSafeProductionConfig } = await import("../src/config/env.js");
    expect(() => assertSafeProductionConfig()).toThrow(/JWT_SECRET/);
  });

  it("throws in production when RAG keys missing", async () => {
    process.env.NODE_ENV = "production";
    process.env.JWT_SECRET = "x".repeat(40);
    delete process.env.RAG_INTERNAL_API_KEY;
    const { assertSafeProductionConfig } = await import("../src/config/env.js");
    expect(() => assertSafeProductionConfig()).toThrow(/RAG_INTERNAL_API_KEY/);
  });

  it("throws in production when ADMIN_BASIC_* missing", async () => {
    process.env.NODE_ENV = "production";
    process.env.JWT_SECRET = "x".repeat(40);
    process.env.RAG_INTERNAL_API_KEY = "internal-key-32-chars-minimum!!";
    process.env.RAG_ADMIN_API_KEY = "admin-key-32-chars-minimum!!!!!";
    delete process.env.ADMIN_BASIC_USER;
    delete process.env.ADMIN_BASIC_PASS;
    const { assertSafeProductionConfig } = await import("../src/config/env.js");
    expect(() => assertSafeProductionConfig()).toThrow(/ADMIN_BASIC/);
  });
});
