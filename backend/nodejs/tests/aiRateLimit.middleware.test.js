import { describe, it, expect } from "vitest";
import express from "express";
import request from "supertest";
import { createAiRateLimitMiddleware } from "../src/middlewares/aiRateLimit.middleware.js";

describe("ai rate limit middleware", () => {
  it("returns 429 after max requests per minute", async () => {
    const app = express();
    app.post("/api/ai/rag-chat", createAiRateLimitMiddleware(2), (_req, res) => {
      res.json({ ok: true });
    });

    await request(app).post("/api/ai/rag-chat").expect(200);
    await request(app).post("/api/ai/rag-chat").expect(200);
    const blocked = await request(app).post("/api/ai/rag-chat").expect(429);
    expect(blocked.body.success).toBe(false);
  });
});
