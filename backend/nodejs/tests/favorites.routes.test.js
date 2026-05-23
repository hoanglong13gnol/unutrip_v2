import { describe, it, expect, vi, beforeEach } from "vitest";
import request from "supertest";

vi.hoisted(() => {
  process.env.JWT_SECRET = "test-jwt-secret-for-favorites-route-tests";
});

const {
  listUserFavorites,
  addUserFavorite,
  removeUserFavorite
} = vi.hoisted(() => ({
  listUserFavorites: vi.fn(async () => [{ id: 1, name: "Favorite place", isFavorite: true }]),
  addUserFavorite: vi.fn(async () => ({ ok: true })),
  removeUserFavorite: vi.fn(async () => ({ ok: true }))
}));

vi.mock("../src/services/favorites.service.js", () => ({
  listUserFavorites,
  addUserFavorite,
  removeUserFavorite
}));

import { createApp } from "../src/app.js";
import { signToken } from "../src/auth.js";

describe("favorites routes", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("GET /api/users/favorites requires auth", async () => {
    const res = await request(createApp()).get("/api/users/favorites");
    expect(res.status).toBe(401);
    expect(listUserFavorites).not.toHaveBeenCalled();
  });

  it("GET /api/users/favorites returns list when authenticated", async () => {
    const token = signToken({ userId: 3, email: "u3@example.com" });
    const res = await request(createApp())
      .get("/api/users/favorites")
      .set("Authorization", `Bearer ${token}`);
    expect(res.status).toBe(200);
    expect(res.body.success).toBe(true);
    expect(res.body.data).toHaveLength(1);
    expect(listUserFavorites).toHaveBeenCalledWith(3);
  });

  it("POST /api/users/favorites rejects invalid payload", async () => {
    const token = signToken({ userId: 3, email: "u3@example.com" });
    const res = await request(createApp())
      .post("/api/users/favorites")
      .set("Authorization", `Bearer ${token}`)
      .send({ destinationId: "not-a-number" });
    expect(res.status).toBe(400);
    expect(addUserFavorite).not.toHaveBeenCalled();
  });

  it("POST /api/users/favorites returns 404 when destination missing", async () => {
    addUserFavorite.mockResolvedValueOnce({ ok: false, reason: "destination_not_found" });
    const token = signToken({ userId: 3, email: "u3@example.com" });
    const res = await request(createApp())
      .post("/api/users/favorites")
      .set("Authorization", `Bearer ${token}`)
      .send({ destinationId: 999 });
    expect(res.status).toBe(404);
    expect(addUserFavorite).toHaveBeenCalledWith(3, 999);
  });

  it("DELETE /api/users/favorites/:destinationId removes favorite", async () => {
    const token = signToken({ userId: 3, email: "u3@example.com" });
    const res = await request(createApp())
      .delete("/api/users/favorites/5")
      .set("Authorization", `Bearer ${token}`);
    expect(res.status).toBe(200);
    expect(res.body.success).toBe(true);
    expect(removeUserFavorite).toHaveBeenCalledWith(3, 5);
  });
});
