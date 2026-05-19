import { describe, it, expect, vi, beforeEach } from "vitest";
import request from "supertest";
import { createApp } from "../src/app.js";

vi.mock("../src/services/ai.service.js", () => ({
  requestRagChatSimple: vi.fn(async () => ({
    ragOk: true,
    data: {
      answer: "Xin chào từ RAG template",
      places: [],
      warnings: [],
      latency_ms: {},
      model_used: "template_no_gemini",
      fallback_used: true,
      rag_mode: "balanced",
      runtime_mode: "demo"
    }
  })),
  requestRagChatFallbackForAiChat: vi.fn(async () => ({
    ok: true,
    answer: "Fallback RAG answer"
  })),
  requestLocalAiChatAnswer: vi.fn(),
  generateSuggestItineraryAiResult: vi.fn(),
  requestItineraryPreview: vi.fn(),
  requestItineraryOptions: vi.fn()
}));

describe("AI chat guest / stale token", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("POST /api/ai/rag-chat works without Authorization", async () => {
    const app = createApp();
    const res = await request(app)
      .post("/api/ai/rag-chat")
      .send({ message: "an gi o ha noi" });
    expect(res.status).toBe(200);
    expect(res.body.success).toBe(true);
    expect(res.body.answer).toContain("RAG");
  });

  it("POST /api/ai/chat works with invalid Bearer token", async () => {
    const app = createApp();
    const res = await request(app)
      .post("/api/ai/chat")
      .set("Authorization", "Bearer not.a.valid.jwt")
      .send({ message: "goi y da nang" });
    expect(res.status).toBe(200);
    expect(res.body.success).toBe(true);
    expect(res.body.answer).toBeTruthy();
  });
});
