import { describe, it, expect, vi, beforeEach } from "vitest";
import request from "supertest";
import { createApp } from "../src/app.js";

vi.mock("../src/services/destinations.service.js", () => ({
  listFeaturedDestinationsForUser: vi.fn(async () => [
    { id: 1, name: "Test Place", is_favorite: 0, rating: 4.5, review_count: 1 }
  ]),
  listDestinationsPage: vi.fn(async () => ({ total: 0, data: [] })),
  listNearbyDestinationsForUser: vi.fn(async () => []),
  getDestinationDetail: vi.fn(async () => ({ ok: false }))
}));

vi.mock("../src/shared/dto/destinationDto.js", async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    attachDestinationImages: vi.fn(async (rows) => rows),
    toDestinationDto: vi.fn((row, isFavorite) => ({
      id: row.id,
      name: row.name,
      isFavorite
    }))
  };
});

describe("GET /api/destinations/featured", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns 200 without Authorization header (guest browse)", async () => {
    const app = createApp();
    const res = await request(app).get("/api/destinations/featured");
    expect(res.status).toBe(200);
    expect(res.body.success).toBe(true);
    expect(Array.isArray(res.body.data)).toBe(true);
  });

  it("returns 200 with invalid token (stale session after DB reset)", async () => {
    const app = createApp();
    const res = await request(app)
      .get("/api/destinations/featured")
      .set("Authorization", "Bearer not.a.valid.jwt");
    expect(res.status).toBe(200);
    expect(res.body.success).toBe(true);
  });
});
