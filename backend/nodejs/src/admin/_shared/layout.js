/**
 * Admin-only shared layout renderer extracted from `src/admin.js` in Phase 4.
 * Phase 6: HTML shell loaded from `src/admin/templates/layout.html` via
 * `adminTemplate.js` — output remains byte-identical when filled with the
 * same `content`, `activePath`, `title`, and optional `cspNonce`.
 */

import { fillAdminTemplate, loadAdminTemplate } from "./adminTemplate.js";
import { escapeHtml } from "./escape.js";
import { isAdminAuthConfigured } from "../../middlewares/adminAuth.middleware.js";

function navPrefix(activePath, name) {
  return activePath === name ? "sidebar-active" : "";
}

function buildAdminFooter(authContext = {}) {
  const { adminUser, authConfigured } = authContext;
  const configured = authConfigured ?? isAdminAuthConfigured();

  if (adminUser) {
    const initials = String(adminUser.username || "AD")
      .slice(0, 2)
      .toUpperCase();
    return `
                <div class="flex items-center justify-between gap-2">
                    <div class="flex items-center space-x-3 min-w-0">
                        <div class="w-10 h-10 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center font-bold text-sm flex-shrink-0">${initials}</div>
                        <div class="min-w-0">
                            <p class="text-sm font-semibold truncate">${escapeHtml(adminUser.username)}</p>
                            <p class="text-xs text-gray-500">Administrator</p>
                        </div>
                    </div>
                    <form method="post" action="/admin/auth/logout" class="flex-shrink-0">
                        <button type="submit" class="text-gray-400 hover:text-red-400 transition p-2 rounded-lg hover:bg-white/5" title="Đăng xuất">
                            <i class="fas fa-sign-out-alt"></i>
                        </button>
                    </form>
                </div>`;
  }

  if (configured) {
    return `
                <a href="/admin/login" class="flex items-center justify-center gap-2 w-full bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold uppercase tracking-wide py-3 rounded-xl transition shadow-lg shadow-blue-500/20">
                    <i class="fas fa-right-to-bracket"></i>
                    <span>Đăng nhập Admin</span>
                </a>`;
  }

  return `
                <div class="flex items-center space-x-3">
                    <div class="w-10 h-10 rounded-full bg-gradient-to-tr from-amber-500 to-orange-600 flex items-center justify-center font-bold text-sm">DV</div>
                    <div>
                        <p class="text-sm font-semibold">Dev mode</p>
                        <p class="text-xs text-amber-400">Chưa bật xác thực</p>
                    </div>
                </div>`;
}

export function layoutFromRequest(req) {
  return { adminUser: req.adminUser ?? null };
}

/**
 * @param {string} content
 * @param {string} activePath
 * @param {string} [title]
 * @param {string} [cspNonce]
 * @param {{ adminUser?: { username: string } | null, authConfigured?: boolean }} [authContext]
 */
export function renderLayout(content, activePath, title = "Quản trị hệ thống", cspNonce, authContext = {}) {
  const base = loadAdminTemplate("layout.html");
  const adminUser = authContext.adminUser ?? null;
  return fillAdminTemplate(base, {
    TITLE: title,
    HEADER_DATE: new Date().toLocaleDateString("vi-VN", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric"
    }),
    NAV_DASHBOARD: navPrefix(activePath, "dashboard"),
    NAV_USERS: navPrefix(activePath, "users"),
    NAV_DESTINATIONS: navPrefix(activePath, "destinations"),
    NAV_REVIEWS: navPrefix(activePath, "reviews"),
    NAV_SYSTEM: navPrefix(activePath, "system"),
    NAV_RAG_AI: navPrefix(activePath, "rag-ai"),
    ADMIN_FOOTER: buildAdminFooter({ ...authContext, adminUser }),
    CONTENT: content
  });
}
