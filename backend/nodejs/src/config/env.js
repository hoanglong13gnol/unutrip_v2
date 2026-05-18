/**
 * Central place for derived env values and production safety checks.
 * Load root `.env` before reading process.env (ESM imports run before index.js body).
 */
import dotenv from "dotenv";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
dotenv.config({ path: path.resolve(__dirname, "../../../../.env") });

const DEFAULT_JWT_SECRET = "smarttravel_dev_secret_change_me";
const MIN_JWT_SECRET_LEN = 32;
const MIN_RAG_KEY_LEN = 16;
const WEAK_SECRET_FRAGMENTS = [
  "changeme",
  "change_me",
  "your_jwt",
  "secret_key",
  "password",
  "paste_your",
  "example",
  "smarttravel_dev_secret",
];

/** Base URL FastAPI RAG. Node admin gọi `/admin/*` qua URL này; nếu RAG bật `RAG_ADMIN_API_KEY`, đặt cùng giá trị trong `RAG_ADMIN_API_KEY` (Node) — gửi qua header `X-RAG-Internal-Key`. */
export const RAG_BASE_URL =
  process.env.RAG_BASE_URL ||
  process.env.RAG_API_BASE ||
  "http://127.0.0.1:8001";

export function getJwtSecret() {
  return process.env.JWT_SECRET || DEFAULT_JWT_SECRET;
}

export function isDefaultJwtSecret() {
  return getJwtSecret() === DEFAULT_JWT_SECRET;
}

function isWeakSecret(value, minLen = MIN_RAG_KEY_LEN) {
  const s = String(value || "").trim();
  if (s.length < minLen) return true;
  const lower = s.toLowerCase();
  return WEAK_SECRET_FRAGMENTS.some((frag) => lower.includes(frag));
}

/**
 * Call once at process startup (before accepting traffic).
 */
export function assertSafeProductionConfig() {
  const nodeEnv = process.env.NODE_ENV || "development";
  if (nodeEnv !== "production") return;

  if (isDefaultJwtSecret() || isWeakSecret(getJwtSecret(), MIN_JWT_SECRET_LEN)) {
    throw new Error(
      "[config] NODE_ENV=production requires a strong JWT_SECRET (>= 32 chars, not the dev default)."
    );
  }

  const internal = process.env.RAG_INTERNAL_API_KEY?.trim();
  const admin = process.env.RAG_ADMIN_API_KEY?.trim();

  if (!internal) {
    throw new Error(
      "[config] NODE_ENV=production requires RAG_INTERNAL_API_KEY (same value on Node and FastAPI RAG)."
    );
  }
  if (isWeakSecret(internal)) {
    throw new Error("[config] RAG_INTERNAL_API_KEY is too short or looks like a placeholder.");
  }

  if (!admin) {
    throw new Error(
      "[config] NODE_ENV=production requires RAG_ADMIN_API_KEY (separate from RAG_INTERNAL_API_KEY)."
    );
  }
  if (isWeakSecret(admin)) {
    throw new Error("[config] RAG_ADMIN_API_KEY is too short or looks like a placeholder.");
  }
  if (admin === internal) {
    throw new Error("[config] RAG_ADMIN_API_KEY must differ from RAG_INTERNAL_API_KEY in production.");
  }

  const ragDebug = String(process.env.RAG_DEBUG || "")
    .trim()
    .toLowerCase();
  if (["1", "true", "yes", "on"].includes(ragDebug)) {
    throw new Error("[config] RAG_DEBUG must be false in production.");
  }
}

function envInt(name, fallback) {
  const raw = process.env[name];
  if (raw === undefined || raw === null || String(raw).trim() === "") return fallback;
  const n = Number.parseInt(String(raw), 10);
  return Number.isFinite(n) ? n : fallback;
}

function envBool(name, fallback = false) {
  const v = process.env[name];
  if (v === undefined || v === null) return fallback;
  return ["1", "true", "yes", "on"].includes(String(v).trim().toLowerCase());
}

/**
 * Behind nginx / load balancer: sets Express `trust proxy` so req.ip and secure cookies behave correctly.
 */
export const TRUST_PROXY = envBool("TRUST_PROXY", false);

/** MySQL pool size (mysql2 connectionLimit). */
export const DB_POOL_CONNECTION_LIMIT = Math.max(1, envInt("DB_POOL_CONNECTION_LIMIT", 10));

/** Max time for a single RAG HTTP request (retrieval + Gemini can be slow). */
export const RAG_FETCH_TIMEOUT_MS = envInt("RAG_FETCH_TIMEOUT_MS", 90_000);

/**
 * Total HTTP attempts per RAG call on transient errors (network, 502/503/504/429).
 * Minimum 1.
 */
export const RAG_FETCH_MAX_ATTEMPTS = Math.max(1, envInt("RAG_FETCH_MAX_ATTEMPTS", 3));

/** Skip RAG probe in GET /api/health/ready (use when RAG is optional in an environment). */
export const HEALTHCHECK_SKIP_RAG = envBool("HEALTHCHECK_SKIP_RAG", false);

/**
 * Phase 7 — v2 place tables only (no legacy `destinations` fallback in place-id resolution).
 * When true, overrides PLACE_ID_LEGACY_FALLBACK to false.
 */
export const USE_V2_PLACE_TABLES = envBool("USE_V2_PLACE_TABLES", false);

/** Allow legacy `destinations` lookups when v2 map misses (default true for old XAMPP schemas). */
export const PLACE_ID_LEGACY_FALLBACK = USE_V2_PLACE_TABLES
  ? false
  : envBool("PLACE_ID_LEGACY_FALLBACK", true);

/** Timeout for optional local AI_MODEL_URL requests. */
export const AI_MODEL_FETCH_TIMEOUT_MS = envInt("AI_MODEL_FETCH_TIMEOUT_MS", 120_000);

/**
 * URL tùy chọn cho LLM cục bộ: `POST` JSON `{ message }` → `{ answer }` (như `backend/nodejs/server.py`).
 * Khi biến môi trường không set, trả `null` — Node **không** gọi `localhost:8000/chat` nữa; dùng thẳng RAG để tránh chờ timeout và log "fetch failed".
 * Đặt `AI_MODEL_URL` (ví dụ `http://127.0.0.1:8000/chat` hoặc `http://127.0.0.1:8001/chat` nếu chỉ có RAG) khi bạn thật sự có service đó.
 */
export function getResolvedAiModelUrl() {
  const raw = process.env.AI_MODEL_URL;
  if (raw === undefined || raw === null) return null;
  const s = String(raw).trim();
  return s.length ? s : null;
}

/** Node admin → FastAPI `/admin/ai/debug-query` (full RAG + Gemini; cần lâu hơn gọi RAG thường). */
export const RAG_ADMIN_DEBUG_TIMEOUT_MS = envInt("RAG_ADMIN_DEBUG_TIMEOUT_MS", 120_000);
