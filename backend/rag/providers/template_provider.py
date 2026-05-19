from __future__ import annotations

from typing import Any


class TemplateAnswerProvider:
    """Deterministic answers when LLM is unavailable or runtime is mock/retrieval-only."""

    def build_mock_answer(self, retrieved: dict[str, Any]) -> str:
        intent = retrieved.get("intent", {})
        results = retrieved.get("results", [])

        if not results:
            return "Mình chưa tìm thấy địa điểm phù hợp trong dữ liệu hiện có."

        names = [item.get("title") for item in results[:5]]

        if intent.get("intent") == "itinerary":
            return (
                "Đây là câu trả lời mock. Pipeline đã truy xuất được các địa điểm phù hợp để lập lịch trình: "
                + ", ".join(names)
                + "."
            )

        return (
            "Đây là câu trả lời mock. Pipeline đã truy xuất được các địa điểm phù hợp: "
            + ", ".join(names)
            + "."
        )

    def build_template_answer(self, retrieved: dict[str, Any]) -> str:
        results = retrieved.get("results", [])

        if not results:
            return "Mình chưa tìm thấy địa điểm phù hợp trong dữ liệu hiện có."

        lines = [
            "Mình đã tìm được một số địa điểm phù hợp từ dữ liệu UnuTrip:",
            "",
        ]

        for index, item in enumerate(results[:5], start=1):
            meta = item.get("metadata") or {}
            name = item.get("title")
            province = meta.get("province")
            walking = meta.get("walking_level_norm")
            budget = meta.get("budget_level_norm")
            budget_label = budget if budget not in (None, "") else "chưa có"
            walking_label = walking if walking not in (None, "") else "chưa có"

            lines.append(
                f"{index}. {name} ({province}) - ngân sách: {budget_label}, mức đi bộ: {walking_label}."
            )

        lines.append("")
        province_hint = ""
        if results:
            first_prov = (results[0].get("metadata") or {}).get("province")
            if first_prov:
                province_hint = f" tại {first_prov}"
        lines.append(
            f"Dựa trên dữ liệu UnuTrip{province_hint}, bạn có thể ưu tiên các điểm phù hợp sở thích "
            "(ẩm thực, văn hóa, thiên nhiên…). Bấm Tạo lịch trình để chỉnh sửa trước khi lưu."
        )

        return "\n".join(lines)
