import { daysBetweenInclusive, toIsoDate } from "../../utils.js";
import {
  generateSuggestItineraryAiResult,
  requestItineraryOptions,
  requestItineraryPreview
} from "../../services/ai.service.js";
import { persistAiSuggestedItinerary } from "../../services/itineraries.service.js";
import { traceHeadersOrFallback } from "./ai.helpers.js";
import {
  itineraryOptionsBodySchema,
  itineraryPreviewBodySchema,
  suggestItineraryBodySchema
} from "./ai.schemas.js";

export async function suggestItinerary(req, res) {
  const parsed = suggestItineraryBodySchema.safeParse(req.body);
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
