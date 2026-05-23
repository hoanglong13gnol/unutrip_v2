import * as itinerariesRepository from "../repositories/itineraries.repository.js";
import * as placeIdMapService from "./placeIdMap.service.js";
import { withTransaction } from "../shared/db/withTransaction.js";
import { DEFAULT_AI_ITINERARY_TIME_SLOTS } from "../shared/utils/timeSlots.js";
import { flattenSelectedOptionDays, resolveDestinationIdsFromSelection } from "../shared/dto/itineraryDto.js";

/**
 * POST /itineraries/create-from-option persistence (wrapped in `withTransaction` in Phase 3), after route field validation.
 *
 * @param {{ userId: number, payload: Record<string, unknown> }} params
 * @returns {Promise<
 *   | { ok: false; reason: "no_mapped_destinations"; optionId: unknown; unresolved: unknown[] }
 *   | { ok: false; reason: "invalid_dates" }
 *   | {
 *       ok: true;
 *       data: {
 *         id: number;
 *         itineraryId: number;
 *         optionId: unknown;
 *         selectedCount: number;
 *         unresolved: unknown[];
 *       };
 *     }
 * >}
 */
export async function createItineraryFromAiOption({ userId, payload }) {
  const {
    title,
    description,
    startDate,
    endDate,
    estimatedBudget,
    budget,
    optionId,
    days
  } = payload;

  const selectedDestinations = flattenSelectedOptionDays(days);

  const resolved = await resolveDestinationIdsFromSelection(selectedDestinations);
  const destinationIds = resolved.destinationIds;
  const unresolved = resolved.unresolved;

  if (destinationIds.length === 0) {
    return {
      ok: false,
      reason: "no_mapped_destinations",
      optionId: optionId ?? null,
      unresolved
    };
  }

  const start = new Date(startDate);
  const end = new Date(endDate);

  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) {
    return { ok: false, reason: "invalid_dates" };
  }

  const totalDays = Math.max(1, Math.floor((end - start) / (1000 * 60 * 60 * 24)) + 1);

  const finalBudget = estimatedBudget ?? budget ?? null;

  const destinationIdByRawPlaceId = new Map();

  for (const item of selectedDestinations) {
    const directId = item?.destinationId ?? item?.destination_id;
    const rawPlaceId = placeIdMapService.extractRawPlaceId(item);

    if (
      directId !== null &&
      directId !== undefined &&
      Number.isInteger(Number(directId)) &&
      Number(directId) > 0
    ) {
      if (rawPlaceId) {
        destinationIdByRawPlaceId.set(rawPlaceId, Number(directId));
      }
    }
  }

  const { resolved: rawPlaceMap } = await placeIdMapService.resolveRawPlaceIdsFromItems(
    selectedDestinations
  );
  for (const [rawPlaceId, destinationId] of rawPlaceMap) {
    if (!destinationIdByRawPlaceId.has(rawPlaceId)) {
      destinationIdByRawPlaceId.set(rawPlaceId, destinationId);
    }
  }

  const timeSlots = DEFAULT_AI_ITINERARY_TIME_SLOTS;

  const { itineraryId, insertedCount } = await withTransaction(async (conn) => {
    const itineraryInfo = await itinerariesRepository.insertItinerary(
      {
        userId,
        title,
        description: description ?? null,
        startDate,
        endDate,
        totalDays,
        estimatedBudget: finalBudget
      },
      conn
    );

    const newItineraryId = Number(itineraryInfo.lastInsertRowid);
    const dayIdByNumber = new Map();

    for (let dayNumber = 1; dayNumber <= totalDays; dayNumber++) {
      const date = new Date(start);
      date.setDate(start.getDate() + dayNumber - 1);

      const dateText = date.toISOString().slice(0, 10);

      const dayInfo = await itinerariesRepository.insertItineraryDay(
        {
          itineraryId: newItineraryId,
          dayNumber,
          date: dateText
        },
        conn
      );

      dayIdByNumber.set(dayNumber, Number(dayInfo.lastInsertRowid));
    }

    let inserted = 0;

    for (const day of days) {
      const dayNumber = Number(day?.dayNumber || 1);
      const dayId = dayIdByNumber.get(dayNumber);

      if (!dayId) continue;

      const items = Array.isArray(day?.items) ? day.items : [];

      for (let index = 0; index < items.length; index++) {
        const item = items[index];
        const rawPlaceId = placeIdMapService.extractRawPlaceId(item);
        const directId = item?.destinationId ?? item?.destination_id;

        let destinationId = null;

        if (
          directId !== null &&
          directId !== undefined &&
          Number.isInteger(Number(directId)) &&
          Number(directId) > 0
        ) {
          destinationId = Number(directId);
        } else if (rawPlaceId) {
          destinationId = destinationIdByRawPlaceId.get(rawPlaceId);
        }

        if (!destinationId) continue;

        const slot = timeSlots[index % timeSlots.length];

        await itinerariesRepository.insertItineraryItem(
          {
            dayId,
            destinationId,
            startTime: item?.startTime || slot[0],
            endTime: item?.endTime || slot[1],
            note: item?.reason || "ÄÆ°á»£c chá»n tá»« AI tour",
            orderIndex: index + 1
          },
          conn
        );

        inserted++;
      }
    }

    return { itineraryId: newItineraryId, insertedCount: inserted };
  });

  return {
    ok: true,
    data: {
      id: itineraryId,
      itineraryId,
      optionId: optionId ?? null,
      selectedCount: insertedCount,
      unresolved
    }
  };
}

/**
 * POST /itineraries/create-from-selection persistence (wrapped in `withTransaction` in Phase 3), after route field validation.
 *
 * @param {{ userId: number, payload: Record<string, unknown> }} params
 * @returns {Promise<
 *   | {
 *       ok: false;
 *       reason: "no_mapped_destinations";
 *       receivedSelectedDestinations: unknown;
 *       receivedSelectedDestinationIds: unknown;
 *       unresolved: unknown[];
 *     }
 *   | { ok: false; reason: "invalid_dates" }
 *   | {
 *       ok: true;
 *       data: {
 *         id: unknown;
 *         itineraryId: unknown;
 *         selectedCount: number;
 *         destinationIds: number[];
 *         unresolved: unknown[];
 *       };
 *     }
 * >}
 */
export async function createItineraryFromAiSelection({ userId, payload }) {
  const {
    title,
    description,
    startDate,
    endDate,
    estimatedBudget,
    budget,
    selectedDestinations,
    selectedDestinationIds
  } = payload;

  let destinationIds = [];
  let unresolved = [];

  if (Array.isArray(selectedDestinationIds) && selectedDestinationIds.length > 0) {
    destinationIds = selectedDestinationIds
      .map((id) => Number(id))
      .filter((id) => Number.isInteger(id) && id > 0);
  } else if (Array.isArray(selectedDestinations) && selectedDestinations.length > 0) {
    const resolved = await resolveDestinationIdsFromSelection(selectedDestinations);
    destinationIds = resolved.destinationIds;
    unresolved = resolved.unresolved;
  }

  if (destinationIds.length === 0) {
    return {
      ok: false,
      reason: "no_mapped_destinations",
      receivedSelectedDestinations: selectedDestinations ?? null,
      receivedSelectedDestinationIds: selectedDestinationIds ?? null,
      unresolved
    };
  }

  const start = new Date(startDate);
  const end = new Date(endDate);

  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) {
    return { ok: false, reason: "invalid_dates" };
  }

  const totalDays = Math.max(1, Math.floor((end - start) / (1000 * 60 * 60 * 24)) + 1);

  const finalBudget = estimatedBudget ?? budget ?? null;

  const timeSlots = DEFAULT_AI_ITINERARY_TIME_SLOTS;

  const itineraryId = await withTransaction(async (conn) => {
    const itineraryInfo = await itinerariesRepository.insertItinerary(
      {
        userId,
        title,
        description: description ?? null,
        startDate,
        endDate,
        totalDays,
        estimatedBudget: finalBudget
      },
      conn
    );

    const newItineraryId = itineraryInfo.lastInsertRowid;
    const dayIds = [];

    for (let dayNumber = 1; dayNumber <= totalDays; dayNumber++) {
      const date = new Date(start);
      date.setDate(start.getDate() + dayNumber - 1);

      const dateText = date.toISOString().slice(0, 10);

      const dayInfo = await itinerariesRepository.insertItineraryDay(
        {
          itineraryId: newItineraryId,
          dayNumber,
          date: dateText
        },
        conn
      );

      dayIds.push(dayInfo.lastInsertRowid);
    }

    for (let i = 0; i < destinationIds.length; i++) {
      const dayIndex = i % totalDays;
      const orderIndex = Math.floor(i / totalDays);
      const slot = timeSlots[orderIndex % timeSlots.length];

      await itinerariesRepository.insertItineraryItem(
        {
          dayId: dayIds[dayIndex],
          destinationId: destinationIds[i],
          startTime: slot[0],
          endTime: slot[1],
          note: "ÄÆ°á»£c chá»n tá»« AI gá»£i Ã½",
          orderIndex: orderIndex + 1
        },
        conn
      );
    }

    return newItineraryId;
  });

  return {
    ok: true,
    data: {
      id: itineraryId,
      itineraryId,
      selectedCount: destinationIds.length,
      destinationIds,
      unresolved
    }
  };
}
