/**
 * Admin auth gate for /admin/*.
 *
 * - When BOTH `ADMIN_BASIC_USER` and `ADMIN_BASIC_PASS` are set:
 *   accepts signed session cookie OR HTTP Basic credentials.
 * - When either env var is missing: passthrough (dev mode) with one-time warning.
 *
 * Unauthenticated HTML requests redirect to `/admin/login`.
 * JSON/API-style admin POSTs return 401 JSON.
 */

import { Buffer } from "node:buffer";
import { timingSafeEqual } from "node:crypto";
import { readAdminSessionFromCookieHeader } from "../admin/_shared/adminSession.js";

let warned = false;

const OPEN_PATHS = new Set(["/login", "/auth/login"]);

export function isAdminAuthConfigured() {
  return Boolean(process.env.ADMIN_BASIC_USER && process.env.ADMIN_BASIC_PASS);
}

function warnOnce() {
  if (warned) return;
  warned = true;
  console.warn(
    "[adminAuth] ADMIN_BASIC_USER/ADMIN_BASIC_PASS not set — /admin is unauthenticated (dev mode)"
  );
}

/** @param {string} a @param {string} b */
export function constantTimeStringEquals(a, b) {
  const bufA = Buffer.from(a, "utf8");
  const bufB = Buffer.from(b, "utf8");
  const len = Math.max(bufA.length, bufB.length);
  const padA = Buffer.alloc(len);
  const padB = Buffer.alloc(len);
  bufA.copy(padA);
  bufB.copy(padB);
  const equal = timingSafeEqual(padA, padB);
  return equal && bufA.length === bufB.length;
}

function sendUnauthorized(res) {
  res.setHeader("WWW-Authenticate", 'Basic realm="UnuTrip Admin"');
  res.status(401).type("text/plain").send("Unauthorized");
}

function sendUnauthorizedJson(res) {
  res.status(401).json({ success: false, message: "Unauthorized" });
}

function verifyBasicAuth(header, user, pass) {
  if (!header || typeof header !== "string" || !header.startsWith("Basic ")) return false;

  let decoded;
  try {
    decoded = Buffer.from(header.slice(6).trim(), "base64").toString("utf8");
  } catch {
    return false;
  }

  const sepIndex = decoded.indexOf(":");
  if (sepIndex < 0) return false;

  const providedUser = decoded.slice(0, sepIndex);
  const providedPass = decoded.slice(sepIndex + 1);

  const userOk = constantTimeStringEquals(providedUser, user);
  const passOk = constantTimeStringEquals(providedPass, pass);
  return userOk && passOk;
}

/**
 * @param {import("express").Request} req
 * @param {import("express").Response} res
 * @param {import("express").NextFunction} next
 */
export function adminAuthMiddleware(req, res, next) {
  const user = process.env.ADMIN_BASIC_USER;
  const pass = process.env.ADMIN_BASIC_PASS;

  const session = readAdminSessionFromCookieHeader(req.headers.cookie);
  if (session) {
    req.adminUser = session;
    return next();
  }

  if (!user || !pass) {
    warnOnce();
    req.adminUser = null;
    return next();
  }

  if (OPEN_PATHS.has(req.path)) {
    req.adminUser = null;
    return next();
  }

  const header = req.headers.authorization;
  if (verifyBasicAuth(header, user, pass)) {
    req.adminUser = { username: user };
    return next();
  }

  const acceptsHtml = (req.headers.accept || "").includes("text/html");
  const isGet = req.method === "GET" || req.method === "HEAD";

  if (isGet && acceptsHtml) {
    const nextPath = encodeURIComponent(req.originalUrl || "/admin/dashboard");
    return res.redirect(302, `/admin/login?next=${nextPath}`);
  }

  const wantsJson =
    req.headers.accept?.includes("application/json") ||
    req.headers["content-type"]?.includes("application/json") ||
    req.path.startsWith("/users/api/") ||
    req.path.startsWith("/destinations/api/") ||
    req.path.startsWith("/reviews/api/") ||
    req.method === "POST";

  if (wantsJson) {
    return sendUnauthorizedJson(res);
  }

  return sendUnauthorized(res);
}

export default adminAuthMiddleware;
