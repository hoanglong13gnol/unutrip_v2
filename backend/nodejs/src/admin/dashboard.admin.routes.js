/**
 * Admin section router: dashboard.
 *
 * Phase 4 split — handler bodies are byte-identical copies of the original
 * `router.get("/dashboard", …)` block in the old `src/admin.js`. The shared
 * `renderLayout` helper now lives in `./_shared/layout.js`.
 */

import { fillAdminTemplate, loadAdminTemplate, scriptNonceAttr } from "./_shared/adminTemplate.js";
import { escapeHtml } from "./_shared/escape.js";
import { adminHtmlErrorMessage } from "./_shared/adminErrors.js";
import { renderLayout, layoutFromRequest } from "./_shared/layout.js";
import { fetchDashboardStats, fetchLatestUsers } from "./dashboard.service.js";

export function registerDashboardAdminRoutes(router) {
  router.get("/", (_req, res) => {
    res.redirect(302, "/admin/dashboard");
  });

  // 1. Dashboard
  router.get("/dashboard", async (req, res) => {
    try {
      const stats = await fetchDashboardStats();
      const latestUsers = await fetchLatestUsers(5);

      const latestUserRows = latestUsers
        .map(
          (u, i) => `
                                <tr class="${i % 2 === 0 ? "bg-white" : "bg-gray-50/40"} hover:bg-blue-50/50 transition duration-150 cursor-pointer">
                                    <td class="px-8 py-5">
                                        <div class="flex items-center">
                                            <div class="w-9 h-9 rounded-full bg-slate-100 flex items-center justify-center text-slate-500 font-bold text-xs mr-3">${escapeHtml(u.full_name.charAt(0))}</div>
                                            <span class="font-semibold text-gray-700">${escapeHtml(u.full_name)}</span>
                                        </div>
                                    </td>
                                    <td class="px-8 py-5 text-gray-600 text-sm font-medium">${escapeHtml(u.email)}</td>
                                    <td class="px-8 py-5 text-center text-xs font-bold text-gray-400">${new Date(u.created_at).toLocaleDateString("vi-VN")}</td>
                                </tr>
                            `
        )
        .join("");

      const cspNonce = res.locals.cspNonce;
      const content = fillAdminTemplate(loadAdminTemplate("dashboard.content.html"), {
        TOTAL_USERS: stats.totalUsers,
        TOTAL_DESTINATIONS: stats.totalDestinations,
        TOTAL_ITINERARIES: stats.totalItineraries,
        LATEST_USER_ROWS: latestUserRows,
        SCRIPT_NONCE_ATTR: scriptNonceAttr(cspNonce)
      });
      res.send(renderLayout(content, "dashboard", undefined, cspNonce, layoutFromRequest(req)));
    } catch (error) {
      res.status(500).send(adminHtmlErrorMessage(error, "Admin dashboard error"));
    }
  });
}
