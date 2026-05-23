import { authMiddleware, optionalAuthMiddleware } from "../../auth.js";
import { AI_RATE_LIMIT_PER_MINUTE } from "../../config/env.js";
import { createAiRateLimitMiddleware } from "../../middlewares/aiRateLimit.middleware.js";
import {
  suggestItinerary,
  ragChat,
  chat,
  itineraryPreview,
  itineraryOptions,
  createFromOption,
  createFromSelection
} from "./ai.controller.js";

/**
 * NOTE: create-from-option and create-from-selection live in the ai module
 * but their public paths must remain under /api/itineraries/* (Android
 * contract). Do not move them to /api/ai/*.
 */
export function registerAiRoutes(router) {
  const aiRateLimit = createAiRateLimitMiddleware(AI_RATE_LIMIT_PER_MINUTE);

  router.post("/ai/suggest-itinerary", aiRateLimit, authMiddleware, suggestItinerary);
  router.post("/ai/rag-chat", aiRateLimit, optionalAuthMiddleware, ragChat);
  router.post("/ai/chat", aiRateLimit, optionalAuthMiddleware, chat);
  router.post("/ai/itinerary-preview", aiRateLimit, authMiddleware, itineraryPreview);
  router.post("/ai/itinerary-options", aiRateLimit, authMiddleware, itineraryOptions);
  router.post("/itineraries/create-from-option", authMiddleware, createFromOption);
  router.post("/itineraries/create-from-selection", authMiddleware, createFromSelection);
}
