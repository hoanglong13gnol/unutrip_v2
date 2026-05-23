import { describe, it, expect, vi, beforeEach } from "vitest";
import request from "supertest";

vi.hoisted(() => {
  process.env.JWT_SECRET = "test-jwt-secret-for-reviews-route-tests";
});

const createReviewMock = vi.fn(async () => ({
  ok: true,
  review: { id: 99, destinationId: 1, rating: 5, comment: "Great" }
}));

const listReviewsForDestinationMock = vi.fn(async () => [
  { id: 1, rating: 5, comment: "Nice", userName: "Demo" }
]);

vi.mock("../src/services/reviews.service.js", () => ({
  createReview: (...args) => createReviewMock(...args),
  listReviewsForDestination: (...args) => listReviewsForDestinationMock(...args)
}));

import { createApp } from "../src/app.js";
import { signToken } from "../src/auth.js";

describe("reviews routes", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("GET /api/destinations/:id/reviews requires auth", async () => {
    const res = await request(createApp()).get("/api/destinations/1/reviews");
    expect(res.status).toBe(401);
    expect(listReviewsForDestinationMock).not.toHaveBeenCalled();
  });

  it("GET /api/destinations/:id/reviews returns list when authenticated", async () => {
    const token = signToken({ userId: 7, email: "u7@example.com" });
    const res = await request(createApp())
      .get("/api/destinations/1/reviews")
      .set("Authorization", `Bearer ${token}`);
    expect(res.status).toBe(200);
    expect(res.body.success).toBe(true);
    expect(res.body.data).toHaveLength(1);
    expect(listReviewsForDestinationMock).toHaveBeenCalledWith(1);
  });

  it("POST /api/reviews rejects invalid rating", async () => {
    const token = signToken({ userId: 7, email: "u7@example.com" });
    const res = await request(createApp())
      .post("/api/reviews")
      .set("Authorization", `Bearer ${token}`)
      .field("destinationId", "1")
      .field("rating", "9")
      .field("comment", "Too high");
    expect(res.status).toBe(400);
    expect(createReviewMock).not.toHaveBeenCalled();
  });

  it("POST /api/reviews creates review when payload valid", async () => {
    const token = signToken({ userId: 7, email: "u7@example.com" });
    const res = await request(createApp())
      .post("/api/reviews")
      .set("Authorization", `Bearer ${token}`)
      .field("destinationId", "1")
      .field("rating", "5")
      .field("comment", "  Tuyệt vời  ");
    expect(res.status).toBe(200);
    expect(res.body.success).toBe(true);
    expect(createReviewMock).toHaveBeenCalledWith(
      expect.objectContaining({
        userId: 7,
        destinationId: 1,
        rating: 5,
        comment: "Tuyệt vời"
      })
    );
  });
});
