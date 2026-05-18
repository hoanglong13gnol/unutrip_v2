import { db } from "../db.js";
import { PLACE_ID_LEGACY_FALLBACK } from "../config/env.js";

const IGNORABLE_MYSQL_ERRORS = new Set(["ER_NO_SUCH_TABLE", "ER_BAD_FIELD_ERROR"]);

function isIgnorableSchemaError(error) {
  const code = error?.code;
  return code ? IGNORABLE_MYSQL_ERRORS.has(code) : false;
}

/**
 * Resolve a RAG / client `rawPlaceId` string to `app_places.id` used by itinerary_items.
 *
 * Order:
 * 1) `place_id_map` — rag_place_id, exact place_key, or RAG_ALIAS_{id} from migration 007
 * 2) Numeric string → row in `app_places` by primary key (v2 first cut aligns ids with legacy)
 * 3) MANUAL_{n} place_key convention from quick_legacy populate
 * 4) Legacy `destinations.id` when PLACE_ID_LEGACY_FALLBACK is enabled (off when USE_V2_PLACE_TABLES=true)
 */
export async function getDestinationIdByRagPlaceId(placeId) {
  const pid = String(placeId ?? "").trim();

  if (!pid) {
    return null;
  }

  try {
    const row = await db.get(
      `
        SELECT new_app_place_id AS destination_id
        FROM place_id_map
        WHERE rag_place_id = ?
           OR place_key = ?
           OR place_key = CONCAT('RAG_ALIAS_', ?)
        LIMIT 1
      `,
      [pid, pid, pid]
    );

    if (row?.destination_id != null) {
      const n = Number(row.destination_id);
      return Number.isFinite(n) && n > 0 ? n : null;
    }
  } catch (error) {
    if (!isIgnorableSchemaError(error)) {
      throw error;
    }
  }

  if (/^\d+$/.test(pid)) {
    const idNum = Number(pid);

    try {
      const ap = await db.get(`SELECT id AS destination_id FROM app_places WHERE id = ? LIMIT 1`, [
        idNum
      ]);

      if (ap?.destination_id != null) {
        return Number(ap.destination_id);
      }
    } catch (error) {
      if (!isIgnorableSchemaError(error)) {
        throw error;
      }
    }

    if (PLACE_ID_LEGACY_FALLBACK) {
      try {
        const legacy = await db.get(`SELECT id AS destination_id FROM destinations WHERE id = ? LIMIT 1`, [
          idNum
        ]);

        if (legacy?.destination_id != null) {
          return Number(legacy.destination_id);
        }
      } catch (error) {
        if (!isIgnorableSchemaError(error)) {
          throw error;
        }
      }
    }
  }

  const manualMatch = /^MANUAL_(\d+)$/i.exec(pid);

  if (manualMatch) {
    const idNum = Number(manualMatch[1]);

    try {
      const ap = await db.get(`SELECT id AS destination_id FROM app_places WHERE id = ? LIMIT 1`, [
        idNum
      ]);

      if (ap?.destination_id != null) {
        return Number(ap.destination_id);
      }
    } catch (error) {
      if (!isIgnorableSchemaError(error)) {
        throw error;
      }
    }

    if (PLACE_ID_LEGACY_FALLBACK) {
      try {
        const legacy = await db.get(`SELECT id AS destination_id FROM destinations WHERE id = ? LIMIT 1`, [
          idNum
        ]);

        if (legacy?.destination_id != null) {
          return Number(legacy.destination_id);
        }
      } catch (error) {
        if (!isIgnorableSchemaError(error)) {
          throw error;
        }
      }
    }
  }

  try {
    const byKey = await db.get(`SELECT id AS destination_id FROM app_places WHERE place_key = ? LIMIT 1`, [
      pid
    ]);

    if (byKey?.destination_id != null) {
      return Number(byKey.destination_id);
    }
  } catch (error) {
    if (!isIgnorableSchemaError(error)) {
      throw error;
    }
  }

  if (PLACE_ID_LEGACY_FALLBACK) {
    try {
      const legacyRag = await db.get(
        `SELECT id AS destination_id FROM destinations WHERE rag_place_id = ? LIMIT 1`,
        [pid]
      );

      if (legacyRag?.destination_id != null) {
        return Number(legacyRag.destination_id);
      }
    } catch (error) {
      if (!isIgnorableSchemaError(error)) {
        throw error;
      }
    }
  }

  try {
    const kb = await db.get(
      `
        SELECT app_place_id AS destination_id
        FROM rag_knowledge_base
        WHERE app_place_id IS NOT NULL
          AND (
            knowledge_key = ?
            OR place_key = ?
          )
        LIMIT 1
      `,
      [pid, pid]
    );

    if (kb?.destination_id != null) {
      const n = Number(kb.destination_id);
      return Number.isFinite(n) && n > 0 ? n : null;
    }
  } catch (error) {
    if (!isIgnorableSchemaError(error)) {
      throw error;
    }
  }

  return null;
}

export async function getAppPlaceIdByRagPlaceId(placeId) {
  return getDestinationIdByRagPlaceId(placeId);
}
