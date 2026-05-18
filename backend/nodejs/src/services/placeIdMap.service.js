/**
 * Phase 7 — batch rawPlaceId → app_places.id resolution with explicit unresolved diagnostics.
 */

import * as placeIdMapRepository from "../repositories/placeIdMap.repository.js";

/**
 * @param {unknown} item
 * @returns {string | null}
 */
export function extractRawPlaceId(item) {
  const raw =
    item?.rawPlaceId ?? item?.raw_place_id ?? item?.placeId ?? item?.place_id ?? null;
  if (raw === null || raw === undefined) return null;
  const s = String(raw).trim();
  return s || null;
}

/**
 * @param {Iterable<unknown>} items
 * @returns {Promise<{ resolved: Map<string, number>, unresolved: string[] }>}
 */
export async function resolveRawPlaceIdsFromItems(items) {
  const rawIds = [];
  for (const item of items) {
    const raw = extractRawPlaceId(item);
    if (raw) rawIds.push(raw);
  }
  return resolveRawPlaceIds(rawIds);
}

/**
 * @param {string[]} rawIds
 * @returns {Promise<{ resolved: Map<string, number>, unresolved: string[] }>}
 */
export async function resolveRawPlaceIds(rawIds) {
  const unique = [...new Set(rawIds.map((x) => String(x).trim()).filter(Boolean))];
  const resolved = new Map();
  const unresolved = [];

  for (const raw of unique) {
    const appPlaceId = await placeIdMapRepository.getDestinationIdByRagPlaceId(raw);
    if (appPlaceId && Number(appPlaceId) > 0) {
      resolved.set(raw, Number(appPlaceId));
    } else {
      unresolved.push(raw);
    }
  }

  return { resolved, unresolved };
}
