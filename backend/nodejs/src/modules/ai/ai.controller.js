import { z } from "zod";
import { getResolvedAiModelUrl } from "../../config/env.js";
import { daysBetweenInclusive, toIsoDate, resolveRequestTrace } from "../../utils.js";
import {
  generateSuggestItineraryAiResult,
  requestItineraryOptions,
  requestItineraryPreview,
  requestLocalAiChatAnswer,
  requestRagChatFallbackForAiChat,
  requestRagChatSimple
} from "../../services/ai.service.js";
import {
  createItineraryFromAiOption,
  createItineraryFromAiSelection,
  persistAiSuggestedItinerary
} from "../../services/itineraries.service.js";

/** @param {import("express").Request} req */
function traceHeadersOrFallback(req) {
  return req.traceHeaders ?? resolveRequestTrace(req.headers).traceHeaders;
}

const itineraryPreviewBodySchema = z.object({
  title: z.string().max(500).optional().nullable(),
  description: z.string().max(20000).optional().nullable(),
  startDate: z.union([z.string().max(64), z.null()]).optional(),
  endDate: z.union([z.string().max(64), z.null()]).optional(),
  budget: z.coerce.number().finite().optional().nullable(),
  preferences: z.union([z.array(z.string()), z.null()]).optional(),
  province: z.string().max(128).optional().nullable()
});

const itineraryOptionsBodySchema = z.object({
  title: z.string().max(500).optional().nullable(),
  description: z.string().max(20000).optional().nullable(),
  startDate: z.string().min(8).max(64),
  endDate: z.string().min(8).max(64),
  budget: z.coerce.number().finite().optional().nullable(),
  preferences: z.union([z.array(z.string()), z.null()]).optional(),
  province: z.string().max(128).optional().nullable()
});

const chatBodySchema = z.object({
  message: z.string().trim().min(1).max(8000)
});

export async function suggestItinerary(req, res) {
  const schema = z.object({
    preferences: z.array(z.string()).min(1),
    startDate: z.string().min(8),
    endDate: z.string().min(8),
    budget: z.number().optional().nullable(),
    startLocation: z.string().optional().nullable()
  });
  const parsed = schema.safeParse(req.body);
  if (!parsed.success) return res.status(400).json({ success: false, message: "Invalid payload" });

  const { preferences, startDate, endDate, budget } = parsed.data;
  const totalDays = daysBetweenInclusive(startDate, endDate);

  try {
    const genResult = await generateSuggestItineraryAiResult({
      preferences,
      startDate,
      endDate,
      budget,
      totalDays,
      userId: req.user.userId,
      traceHeaders: traceHeadersOrFallback(req)
    });

    if (!genResult.ok && genResult.reason === "invalid_ai_json") {
      console.error("AI JSON Parse Error:", genResult.error, genResult.raw);
      return res.status(500).json({ success: false, message: "AI trả về dữ liệu không hợp lệ." });
    }

    const aiResult = genResult.aiResult;

    const isoStart = toIsoDate(startDate);
    const isoEnd = toIsoDate(endDate);

    const newItin = await persistAiSuggestedItinerary({
      userId: req.user.userId,
      aiResult,
      isoStart,
      isoEnd,
      totalDays,
      budget
    });

    return res.json({ success: true, itinerary: newItin, message: "Đã tạo lịch trình bằng AI thành công!" });
  } catch (error) {
    console.error("AI Itinerary Suggestion Error:", error);
    return res.status(500).json({ success: false, message: "Lỗi tạo lịch trình tự động: " + error.message });
  }
}

export async function ragChat(req, res) {
  const ragChatSchema = z.object({
    message: z.string().trim().min(1).max(8000),
    top_k: z.coerce.number().int().min(1).max(10).optional(),
    mode: z.string().trim().max(64).optional(),
    targetProvince: z.string().trim().max(128).nullable().optional(),
    targetCity: z.string().trim().max(128).nullable().optional()
  });

  const parsed = ragChatSchema.safeParse(req.body);
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
    return res.status(502).json({
      success: false,
      message: "Không gọi được FastAPI RAG",
      error: error.message
    });
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
    return res.status(500).json({ success: false, message: error.message });
  }
}

export async function itineraryPreview(req, res) {
  try {
    const parsed = itineraryPreviewBodySchema.safeParse(req.body);
    if (!parsed.success) {
      return res.status(400).json({
        success: false,
        message: "Payload không hợp lệ",
        errors: parsed.error.flatten()
      });
    }

    const { title, description, startDate, endDate, budget, preferences, province } = parsed.data;

    const result = await requestItineraryPreview(
      {
        title,
        description,
        startDate,
        endDate,
        budget,
        preferences,
        province
      },
      traceHeadersOrFallback(req)
    );

    if (!result.ok) {
      const { data } = result;
      return res.status(502).json({
        success: false,
        message: data.message || "AI service không trả được gợi ý",
        detail: data
      });
    }

    return res.json(result.data);
  } catch (error) {
    console.error("[AI_PREVIEW_ERROR]", error);
    return res.status(500).json({
      success: false,
      message: "Lỗi preview lịch trình AI: " + error.message
    });
  }
}

export async function itineraryOptions(req, res) {
  try {
    const parsed = itineraryOptionsBodySchema.safeParse(req.body);
    if (!parsed.success) {
      return res.status(400).json({
        success: false,
        message: "Payload không hợp lệ",
        errors: parsed.error.flatten(),
        data: null
      });
    }

    const { title, description, startDate, endDate, budget, preferences, province } = parsed.data;

    const result = await requestItineraryOptions(
      {
        title,
        description,
        startDate,
        endDate,
        budget,
        preferences: Array.isArray(preferences) ? preferences : [],
        province
      },
      traceHeadersOrFallback(req)
    );

    if (!result.ok) {
      const { data } = result;
      return res.status(502).json({
        success: false,
        message: data?.message || "AI service không trả được phương án tour",
        data: null,
        detail: data
      });
    }

    return res.json(result.data);
  } catch (error) {
    console.error("[AI_ITINERARY_OPTIONS_ERROR]", error);

    return res.status(500).json({
      success: false,
      message: "Lỗi lấy phương án tour AI: " + error.message,
      data: null
    });
  }
}

export async function createFromOption(req, res) {
  try {
    const { title, startDate, endDate, days } = req.body;

    if (!title || !startDate || !endDate) {
      return res.status(400).json({
        success: false,
        message: "Thiếu tên lịch trình hoặc ngày đi/ngày về",
        data: null
      });
    }

    if (!Array.isArray(days) || days.length === 0) {
      return res.status(400).json({
        success: false,
        message: "Tour chưa có danh sách ngày/địa điểm",
        data: null
      });
    }

    const result = await createItineraryFromAiOption({
      userId: req.user.userId,
      payload: req.body
    });

    if (!result.ok && result.reason === "no_mapped_destinations") {
      return res.status(400).json({
        success: false,
        message: "Không map được địa điểm nào sang destinations.id",
        data: {
          optionId: result.optionId ?? null,
          unresolved: result.unresolved
        }
      });
    }

    if (!result.ok && result.reason === "invalid_dates") {
      return res.status(400).json({
        success: false,
        message: "Ngày đi/ngày về không hợp lệ",
        data: null
      });
    }

    return res.json({
      success: true,
      message: "Tạo lịch trình từ tour AI thành công",
      data: result.data
    });
  } catch (error) {
    console.error("[CREATE_FROM_OPTION_ERROR]", error);

    return res.status(500).json({
      success: false,
      message: "Lỗi tạo lịch trình từ tour AI: " + error.message,
      data: null
    });
  }
}

export async function createFromSelection(req, res) {
  try {
    const { title, startDate, endDate } = req.body;

    if (!title || !startDate || !endDate) {
      return res.status(400).json({
        success: false,
        message: "Thiếu tên lịch trình hoặc ngày đi/ngày về",
        data: null
      });
    }

    const result = await createItineraryFromAiSelection({
      userId: req.user.userId,
      payload: req.body
    });

    if (!result.ok && result.reason === "no_mapped_destinations") {
      return res.status(400).json({
        success: false,
        message: "Không map được địa điểm nào sang destinations.id",
        data: {
          receivedSelectedDestinations: result.receivedSelectedDestinations ?? null,
          receivedSelectedDestinationIds: result.receivedSelectedDestinationIds ?? null,
          unresolved: result.unresolved
        }
      });
    }

    if (!result.ok && result.reason === "invalid_dates") {
      return res.status(400).json({
        success: false,
        message: "Ngày đi/ngày về không hợp lệ",
        data: null
      });
    }

    return res.json({
      success: true,
      message: "Tạo lịch trình từ AI gợi ý thành công",
      data: result.data
    });
  } catch (error) {
    console.error("[CREATE_FROM_SELECTION_ERROR]", error);

    return res.status(500).json({
      success: false,
      message: "Lỗi tạo lịch trình từ lựa chọn: " + error.message,
      data: null
    });
  }
}
