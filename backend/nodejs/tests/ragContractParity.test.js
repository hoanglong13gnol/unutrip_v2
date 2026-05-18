import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { normalizeRagChatSimpleResponse } from "../src/schemas/ragContract.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const FIXTURE = path.resolve(__dirname, "../../../docs/v2/fixtures/rag_chat_simple_sample.json");

describe("RAG Node contract parity (shared fixture)", () => {
  it("validates docs/v2/fixtures/rag_chat_simple_sample.json", () => {
    const raw = JSON.parse(readFileSync(FIXTURE, "utf8"));
    const out = normalizeRagChatSimpleResponse(raw);
    expect(out.ok).toBe(true);
    expect(out.issues).toHaveLength(0);
    expect(out.data.places[0].place_id).toBe("FIX_KH_BEACH_01");
    expect(out.data.answer).toContain("Khánh Hòa");
  });
});
