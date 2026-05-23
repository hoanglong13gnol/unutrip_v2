/**
 * Admin section router: reviews (đánh giá).
 */

import { parseJsonArray } from "../utils.js";
import { withTransaction } from "../shared/db/withTransaction.js";
import * as reviewsRepository from "../repositories/reviews.repository.js";
import { fillAdminTemplate, loadAdminTemplate, scriptNonceAttr } from "./_shared/adminTemplate.js";
import { escapeHtml } from "./_shared/escape.js";
import { adminErrorMessage } from "./_shared/adminErrors.js";
import { renderLayout, layoutFromRequest } from "./_shared/layout.js";

function renderStars(rating) {
  const n = Math.max(0, Math.min(5, Number(rating) || 0));
  const full = Math.round(n);
  return `<span class="text-orange-500 font-bold text-sm">${"★".repeat(full)}${"☆".repeat(5 - full)}</span>`;
}

function truncateComment(text, max = 80) {
  const s = String(text || "").trim();
  if (!s) return "—";
  if (s.length <= max) return escapeHtml(s);
  return `${escapeHtml(s.slice(0, max))}…`;
}

function renderImageCount(imagesJson) {
  const images = parseJsonArray(imagesJson, []);
  if (!images.length) return "—";
  return `<span class="text-blue-600 text-xs font-bold"><i class="fas fa-image mr-1"></i>${images.length}</span>`;
}

export function registerReviewsAdminRoutes(router) {
  router.get("/reviews", async (req, res) => {
    try {
      const rawQ = typeof req.query.q === "string" ? req.query.q.trim() : "";
      const searchQ = escapeHtml(rawQ);

      let reviews;
      if (rawQ) {
        const like = `%${rawQ}%`;
        reviews = await reviewsRepository.searchAdminReviews({ like });
      } else {
        reviews = await reviewsRepository.listAdminReviews();
      }

      const clearFilterLink = rawQ
        ? `<a href="/admin/reviews" class="inline-flex items-center justify-center bg-white border border-gray-200 text-gray-600 text-xs font-bold px-4 py-2.5 rounded-xl hover:bg-gray-50 transition uppercase whitespace-nowrap">Xóa lọc</a>`
        : "";

      const reviewRows =
        (reviews.length === 0
          ? `<tr><td colspan="8" class="px-8 py-12 text-center text-gray-400 text-sm">Không có đánh giá phù hợp.</td></tr>`
          : "") +
        reviews
          .map(
            (r) => `
                            <tr class="hover:bg-blue-50/50 transition">
                                <td class="px-8 py-4 text-gray-400 font-bold text-xs">${r.id}</td>
                                <td class="px-8 py-4 font-semibold text-gray-700">${escapeHtml(r.user_name)}</td>
                                <td class="px-8 py-4 text-gray-600 text-sm">${escapeHtml(r.place_name)}</td>
                                <td class="px-8 py-4 text-center">${renderStars(r.rating)}</td>
                                <td class="px-8 py-4 text-gray-600 text-sm max-w-xs">${truncateComment(r.comment)}</td>
                                <td class="px-8 py-4 text-center">${renderImageCount(r.images_json)}</td>
                                <td class="px-8 py-4 text-center text-xs font-bold text-gray-400">${new Date(r.created_at).toLocaleDateString("vi-VN")}</td>
                                <td class="px-8 py-4 text-center">
                                    <button type="button" onclick="showReviewModal(${r.id})" class="text-blue-400 hover:text-blue-600 transition p-2 mr-1" title="Sửa"><i class="fas fa-edit"></i></button>
                                    <button type="button" onclick="deleteReview(${r.id})" class="text-red-400 hover:text-red-600 transition p-2" title="Xóa"><i class="fas fa-trash-can"></i></button>
                                </td>
                            </tr>
                        `
          )
          .join("");

      const cspNonce = res.locals.cspNonce;
      const content = fillAdminTemplate(loadAdminTemplate("reviews.content.html"), {
        SEARCH_Q: searchQ,
        CLEAR_FILTER_LINK: clearFilterLink,
        REVIEW_COUNT: reviews.length,
        REVIEW_ROWS: reviewRows,
        SCRIPT_NONCE_ATTR: scriptNonceAttr(cspNonce)
      });
      res.send(renderLayout(content, "reviews", "Quản lý Đánh giá", cspNonce, layoutFromRequest(req)));
    } catch (e) {
      res.status(500).send(adminErrorMessage(e));
    }
  });

  router.get("/reviews/api/:id", async (req, res) => {
    try {
      const id = Number(req.params.id);
      if (!Number.isFinite(id) || id <= 0) {
        return res.status(400).json({ success: false, message: "ID không hợp lệ" });
      }
      const review = await reviewsRepository.getAdminReviewById(id);
      if (!review) return res.status(404).json({ success: false, message: "Không tìm thấy đánh giá" });

      return res.json({
        ...review,
        images: parseJsonArray(review.images_json, null)
      });
    } catch (e) {
      return res.status(500).json({ success: false, message: adminErrorMessage(e) });
    }
  });

  router.post("/reviews/save", async (req, res) => {
    try {
      const body = req.body || {};
      const id = Number(body.id);
      const rating = Number(body.rating);
      const comment = String(body.comment || "").trim();

      if (!Number.isFinite(id) || id <= 0) {
        return res.status(400).json({ success: false, message: "ID không hợp lệ" });
      }
      if (!Number.isFinite(rating) || rating < 1 || rating > 5) {
        return res.status(400).json({ success: false, message: "Điểm đánh giá phải từ 1 đến 5" });
      }
      if (!comment) {
        return res.status(400).json({ success: false, message: "Nội dung đánh giá không được để trống" });
      }

      await withTransaction(async (conn) => {
        const destinationId = await reviewsRepository.adminUpdateReview({ id, rating, comment }, conn);
        if (!destinationId) {
          const err = new Error("Không tìm thấy đánh giá");
          err.statusCode = 404;
          throw err;
        }
        await reviewsRepository.recalculateDestinationReviewAggregate(destinationId, conn);
      });

      return res.json({ success: true });
    } catch (e) {
      const status = e.statusCode === 404 ? 404 : 500;
      const msg =
        status === 404
          ? e.message || "Không tìm thấy đánh giá"
          : adminErrorMessage(e, "Không lưu được đánh giá");
      return res.status(status).json({ success: false, message: msg });
    }
  });

  router.post("/reviews/delete/:id", async (req, res) => {
    try {
      const id = Number(req.params.id);
      if (!Number.isFinite(id) || id <= 0) {
        return res.status(400).json({ success: false, message: "ID không hợp lệ" });
      }

      await withTransaction(async (conn) => {
        const destinationId = await reviewsRepository.deleteReviewById(id, conn);
        if (!destinationId) {
          const err = new Error("Không tìm thấy đánh giá");
          err.statusCode = 404;
          throw err;
        }
        await reviewsRepository.recalculateDestinationReviewAggregate(destinationId, conn);
      });

      return res.json({ success: true });
    } catch (e) {
      const status = e.statusCode === 404 ? 404 : 500;
      const msg =
        status === 404
          ? e.message || "Không tìm thấy đánh giá"
          : adminErrorMessage(e, "Không xóa được đánh giá");
      return res.status(status).json({ success: false, message: msg });
    }
  });
}
