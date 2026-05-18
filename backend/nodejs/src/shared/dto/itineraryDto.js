/**
 * Itinerary DTO module — Phase 5 split of `src/routes/helpers.js`.
 *
 * Function bodies are byte-identical copies of the originals. The only
 * mechanical change is the `placeIdMapRepository` import path, which
 * grows one extra `..` segment because the new file lives one directory
 * deeper than the old `routes/helpers.js`.
 */

import * as placeIdMapService from "../../services/placeIdMap.service.js";

export function flattenSelectedOptionDays(days) {
  const selectedDestinations = [];

  for (const day of days || []) {
    const dayNumber = Number(day?.dayNumber || 1);
    const items = Array.isArray(day?.items) ? day.items : [];

    for (const item of items) {
      selectedDestinations.push({
        ...item,
        recommendedDay: dayNumber
      });
    }
  }

  return selectedDestinations;
}

export async function resolveDestinationIdsFromSelection(selectedDestinations) {
  const resolvedIds = [];
  const unresolved = [];
  const pending = [];

  for (const item of selectedDestinations || []) {
    const directId = item?.destinationId ?? item?.destination_id;

    if (
      directId !== null &&
      directId !== undefined &&
      Number.isInteger(Number(directId)) &&
      Number(directId) > 0
    ) {
      resolvedIds.push(Number(directId));
      continue;
    }

    const rawPlaceId = placeIdMapService.extractRawPlaceId(item);
    if (!rawPlaceId) {
      unresolved.push({
        item,
        reason: "missing rawPlaceId/destinationId"
      });
      continue;
    }

    pending.push({ item, rawPlaceId });
  }

  const { resolved } = await placeIdMapService.resolveRawPlaceIds(pending.map((p) => p.rawPlaceId));

  for (const { rawPlaceId } of pending) {
    const appPlaceId = resolved.get(rawPlaceId);
    if (!appPlaceId) {
      unresolved.push({
        rawPlaceId,
        reason: "not found in place_id_map or app_places"
      });
      continue;
    }
    resolvedIds.push(Number(appPlaceId));
  }

  return {
    destinationIds: [...new Set(resolvedIds)],
    unresolved
  };
}

export function itineraryRowToDto(row, days) {
  return {
    id: row.id,
    userId: row.user_id,
    title: row.title,
    description: row.description ?? null,
    startDate: row.start_date,
    endDate: row.end_date,
    totalDays: row.total_days,
    status: row.status,
    days: days ?? null,
    estimatedBudget: row.estimated_budget ?? null,
    createdAt: row.created_at
  };
}
