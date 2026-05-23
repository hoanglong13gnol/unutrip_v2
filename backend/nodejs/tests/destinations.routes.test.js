import { describe, it, expect, vi, beforeEach } from "vitest";
import request from "supertest";

const { listDestinationsPage, listNearbyDestinationsForUser } = vi.hoisted(() => ({
  listDestinationsPage: vi.fn(async () => ({
    total: 2,
    data: [
      { id: 1, name: "Bãi Dài", province: "Khánh Hòa" },
      { id: 2, name: "Tháp Bà", province: "Khánh Hòa" }
    ]
  })),
  listNearbyDestinationsForUser: vi.fn(async () => [{ id: 3, name: "Nearby spot" }])
}));

vi.mock("../src/services/destinations.service.js", () => ({
  listDestinationsPage,
  listFeaturedDestinationsForUser: vi.fn(async () => []),
  listNearbyDestinationsForUser,
  getDestinationDetail: vi.fn(async () => ({ ok: false }))
}));

vi.mock("../src/shared/dto/destinationDto.js", async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    attachDestinationImages: vi.fn(async (rows) => rows),
    toDestinationDto: vi.fn((row) => row)
  };
});

import { createApp } from "../src/app.js";

describe("GET /api/destinations", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns paginated list for guest", async () => {
    const app = createApp();
    const res = await request(app).get("/api/destinations?page=1&limit=10&province=Khánh%20Hòa");
    expect(res.status).toBe(200);
    expect(res.body.success).toBe(true);
    expect(res.body.total).toBe(2);
    expect(res.body.page).toBe(1);
    expect(res.body.limit).toBe(10);
    expect(listDestinationsPage).toHaveBeenCalledWith(
      expect.objectContaining({
        userId: null,
        province: "Khánh Hòa",
        limit: 10,
        offset: 0
      })
    );
  });

  it("returns 400 for nearby when lat/lng missing", async () => {
    const app = createApp();
    const res = await request(app).get("/api/destinations/nearby?lat=abc&lng=12");
    expect(res.status).toBe(400);
    expect(res.body.success).toBe(false);
    expect(listNearbyDestinationsForUser).not.toHaveBeenCalled();
  });

  it("returns nearby results when coordinates valid", async () => {
    const app = createApp();
    const res = await request(app).get("/api/destinations/nearby?lat=12.25&lng=109.18&radiusKm=10");
    expect(res.status).toBe(200);
    expect(res.body.success).toBe(true);
    expect(res.body.data).toHaveLength(1);
    expect(res.body.center).toEqual({ lat: 12.25, lng: 109.18 });
    expect(listNearbyDestinationsForUser).toHaveBeenCalledWith(
      expect.objectContaining({ lat: 12.25, lng: 109.18, radiusKm: 10 })
    );
  });
});
