import { z } from "zod";

export const suggestItineraryBodySchema = z.object({
  preferences: z.array(z.string()).min(1),
  startDate: z.string().min(8),
  endDate: z.string().min(8),
  budget: z.number().optional().nullable(),
  startLocation: z.string().optional().nullable()
});

export const ragChatBodySchema = z.object({
  message: z.string().trim().min(1).max(8000),
  top_k: z.coerce.number().int().min(1).max(10).optional(),
  mode: z.string().trim().max(64).optional(),
  targetProvince: z.string().trim().max(128).nullable().optional(),
  targetCity: z.string().trim().max(128).nullable().optional()
});

export const chatBodySchema = z.object({
  message: z.string().trim().min(1).max(8000)
});

export const itineraryPreviewBodySchema = z.object({
  title: z.string().max(500).optional().nullable(),
  description: z.string().max(20000).optional().nullable(),
  startDate: z.union([z.string().max(64), z.null()]).optional(),
  endDate: z.union([z.string().max(64), z.null()]).optional(),
  budget: z.coerce.number().finite().optional().nullable(),
  preferences: z.union([z.array(z.string()), z.null()]).optional(),
  province: z.string().max(128).optional().nullable()
});

export const itineraryOptionsBodySchema = z.object({
  title: z.string().max(500).optional().nullable(),
  description: z.string().max(20000).optional().nullable(),
  startDate: z.string().min(8).max(64),
  endDate: z.string().min(8).max(64),
  budget: z.coerce.number().finite().optional().nullable(),
  preferences: z.union([z.array(z.string()), z.null()]).optional(),
  province: z.string().max(128).optional().nullable()
});
