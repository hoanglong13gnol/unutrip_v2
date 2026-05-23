import { describe, it, expect, vi, beforeEach } from "vitest";
import request from "supertest";
import express from "express";

const { dbGet, dbQuery } = vi.hoisted(() => ({
  dbGet: vi.fn(),
  dbQuery: vi.fn()
}));

vi.mock("../src/db.js", () => ({
  db: {
    get: dbGet,
    query: dbQuery,
    run: vi.fn(),
    pool: { query: vi.fn() }
  }
}));

vi.mock("../src/admin/_shared/adminTemplate.js", () => ({
  fillAdminTemplate: (_tpl, vars) => vars.LATEST_USER_ROWS || "",
  loadAdminTemplate: () => "",
  scriptNonceAttr: () => ""
}));

vi.mock("../src/admin/_shared/layout.js", () => ({
  renderLayout: (content) => content,
  layoutFromRequest: () => ({})
}));

import { registerDashboardAdminRoutes } from "../src/admin/dashboard.admin.routes.js";

describe("admin dashboard XSS", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    dbGet.mockResolvedValue({
      totalUsers: 1,
      totalDestinations: 1,
      totalItineraries: 0
    });
    dbQuery.mockResolvedValue([
      {
        full_name: "<script>alert(1)</script>",
        email: "evil@example.com",
        created_at: new Date("2026-01-01T00:00:00.000Z")
      }
    ]);
  });

  it("escapes user full_name and email in latest users rows", async () => {
    const router = express.Router();
    registerDashboardAdminRoutes(router);
    const app = express();
    app.use((req, res, next) => {
      res.locals.cspNonce = "test-nonce";
      next();
    });
    app.use("/admin", router);

    const res = await request(app).get("/admin/dashboard").expect(200);

    expect(res.text).not.toContain("<script>alert(1)</script>");
    expect(res.text).toContain("&lt;script&gt;alert(1)&lt;/script&gt;");
    expect(res.text).toContain("evil@example.com");
    expect(res.text).not.toMatch(/<span[^>]*>evil@example\.com<\/span>/);
  });
});
