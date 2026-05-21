import jwt from "jsonwebtoken";
import { getJwtSecret } from "../../config/env.js";

export const ADMIN_SESSION_COOKIE = "admin_session";
const ADMIN_SESSION_TTL = "24h";

/** @param {string} username */
export function signAdminSession(username) {
  return jwt.sign({ role: "admin", sub: username }, getJwtSecret(), { expiresIn: ADMIN_SESSION_TTL });
}

/** @param {string | undefined | null} token */
export function verifyAdminSession(token) {
  if (!token || typeof token !== "string") return null;
  try {
    const decoded = jwt.verify(token, getJwtSecret());
    if (!decoded || decoded.role !== "admin" || typeof decoded.sub !== "string") return null;
    return { username: decoded.sub };
  } catch {
    return null;
  }
}

/** @param {string | undefined} cookieHeader */
export function readAdminSessionFromCookieHeader(cookieHeader) {
  if (!cookieHeader) return null;
  for (const part of cookieHeader.split(";")) {
    const trimmed = part.trim();
    if (!trimmed.startsWith(`${ADMIN_SESSION_COOKIE}=`)) continue;
    const raw = trimmed.slice(ADMIN_SESSION_COOKIE.length + 1);
    try {
      return verifyAdminSession(decodeURIComponent(raw));
    } catch {
      return null;
    }
  }
  return null;
}

export function adminSessionCookieOptions() {
  const secure = process.env.NODE_ENV === "production";
  return {
    httpOnly: true,
    secure,
    sameSite: "lax",
    path: "/admin",
    maxAge: 24 * 60 * 60 * 1000
  };
}
