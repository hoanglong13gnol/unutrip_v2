/**
 * Admin authentication routes — session cookie login/logout.
 * Login UI lives at `/admin/login`; sidebar logout at bottom-left via layout.
 */

import { fillAdminTemplate, loadAdminTemplate, scriptNonceAttr } from "./_shared/adminTemplate.js";
import { escapeHtml } from "./_shared/escape.js";
import {
  ADMIN_SESSION_COOKIE,
  adminSessionCookieOptions,
  signAdminSession
} from "./_shared/adminSession.js";
import { constantTimeStringEquals, isAdminAuthConfigured } from "../middlewares/adminAuth.middleware.js";

function renderLoginPage({ error, nextPath, cspNonce }) {
  const safeNext = nextPath.startsWith("/admin") && !nextPath.startsWith("/admin/login") ? nextPath : "/admin/dashboard";
  const errorBlock = error
    ? `<div class="mb-4 rounded-xl bg-red-50 border border-red-100 text-red-600 text-sm px-4 py-3 font-medium">${escapeHtml(error)}</div>`
    : "";
  const html = fillAdminTemplate(loadAdminTemplate("login.html"), {
    ERROR_BLOCK: errorBlock,
    NEXT_PATH: escapeHtml(safeNext),
    SCRIPT_NONCE_ATTR: scriptNonceAttr(cspNonce)
  });
  return html;
}

export function registerAuthAdminRoutes(router) {
  router.get("/login", (req, res) => {
    if (!isAdminAuthConfigured()) {
      return res.redirect(302, "/admin/dashboard");
    }
    if (req.adminUser) {
      const nextPath = typeof req.query.next === "string" ? req.query.next : "/admin/dashboard";
      const safeNext = nextPath.startsWith("/admin") ? nextPath : "/admin/dashboard";
      return res.redirect(302, safeNext);
    }
    const nextPath = typeof req.query.next === "string" ? req.query.next : "/admin/dashboard";
    const error = typeof req.query.error === "string" ? req.query.error : "";
    res.send(renderLoginPage({ error, nextPath, cspNonce: res.locals.cspNonce }));
  });

  router.post("/auth/login", (req, res) => {
    if (!isAdminAuthConfigured()) {
      return res.redirect(302, "/admin/dashboard");
    }

    const body = req.body || {};
    const username = String(body.username || "").trim();
    const password = String(body.password || "");
    const nextPathRaw = String(body.next || "/admin/dashboard").trim();
    const nextPath =
      nextPathRaw.startsWith("/admin") && !nextPathRaw.startsWith("/admin/login")
        ? nextPathRaw
        : "/admin/dashboard";

    const expectedUser = process.env.ADMIN_BASIC_USER;
    const expectedPass = process.env.ADMIN_BASIC_PASS;

    const userOk = constantTimeStringEquals(username, expectedUser);
    const passOk = constantTimeStringEquals(password, expectedPass);

    if (!userOk || !passOk) {
      const err = encodeURIComponent("Tên đăng nhập hoặc mật khẩu không đúng");
      return res.redirect(302, `/admin/login?error=${err}&next=${encodeURIComponent(nextPath)}`);
    }

    const token = signAdminSession(username);
    res.cookie(ADMIN_SESSION_COOKIE, token, adminSessionCookieOptions());
    return res.redirect(302, nextPath);
  });

  router.post("/auth/logout", (req, res) => {
    res.clearCookie(ADMIN_SESSION_COOKIE, { path: "/admin" });
    if (isAdminAuthConfigured()) {
      return res.redirect(302, "/admin/login");
    }
    return res.redirect(302, "/admin/dashboard");
  });
}
