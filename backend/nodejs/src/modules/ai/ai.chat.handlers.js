import { getResolvedAiModelUrl } from "../../config/env.js";
import {
  requestLocalAiChatAnswer,
  requestRagChatFallbackForAiChat,
  requestRagChatSimple
} from "../../services/ai.service.js";
import { traceHeadersOrFallback } from "./ai.helpers.js";
import { chatBodySchema, ragChatBodySchema } from "./ai.schemas.js";

export async function ragChat(req, res) {
  const parsed = ragChatBodySchema.safeParse(req.body);
  if (!parsed.success) {
    return res.status(400).json({
      success: false,
      message: "Payload không hợp lệ",
      errors: parsed.error.flatten()
    });
  }

  try {
    const { message, top_k: topK = 6, mode = "balanced", targetProvince, targetCity } = parsed.data;

    const { ragOk, data } = await requestRagChatSimple(
      {
        message,
        top_k: topK,
        mode,
        targetProvince: targetProvince ?? null,
        targetCity: targetCity ?? null
      },
      traceHeadersOrFallback(req)
    );

    if (!ragOk) {
      return res.status(502).json({
        success: false,
        message: "FastAPI RAG trả lỗi",
        data
      });
    }

    return res.json({
      success: true,
      message: "OK",
      answer: data?.answer || "",
      places: data?.places || [],
      warnings: data?.warnings || [],
      latency_ms: data?.latency_ms || null,
      model_used: data?.model_used || null,
      fallback_used: data?.fallback_used ?? null,
      rag_mode: data?.rag_mode || mode,
      runtime_mode: data?.runtime_mode || null,
      raw: data
    });
  } catch (error) {
    const payload = {
      success: false,
      message: "Không gọi được FastAPI RAG"
    };
    if (process.env.NODE_ENV !== "production") {
      payload.error = error.message;
    }
    return res.status(502).json(payload);
  }
}

export async function chat(req, res) {
  try {
    const parsed = chatBodySchema.safeParse(req.body);
    if (!parsed.success) {
      return res.status(400).json({
        success: false,
        message: "Payload không hợp lệ",
        errors: parsed.error.flatten()
      });
    }

    const { message } = parsed.data;
    const aiUrl = getResolvedAiModelUrl();
    const traceHeaders = traceHeadersOrFallback(req);

    if (aiUrl) {
      try {
        const { answer } = await requestLocalAiChatAnswer({ aiUrl, message });
        return res.json({ success: true, answer });
      } catch (err) {
        console.warn("Local AI failed, fallback to RAG:", err.message);
      }
    }

    const result = await requestRagChatFallbackForAiChat({ message, traceHeaders });

    if (!result.ok && result.reason === "invalid_json") {
      return res.status(502).json({
        success: false,
        message: "RAG trả về không hợp lệ"
      });
    }
    if (!result.ok && result.reason === "upstream") {
      return res.status(502).json({
        success: false,
        message: result.message
      });
    }
    return res.json({ success: true, answer: result.answer });
  } catch (error) {
    const message =
      process.env.NODE_ENV === "production" ? "Server error" : error.message;
    return res.status(500).json({ success: false, message });
  }
}
