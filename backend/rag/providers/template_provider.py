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

            lines.append(
                f"{index}. {name} ({province}) - ngân sách: {budget}, mức đi bộ: {walking}."
            )

        lines.append("")
        lines.append(
            "Dựa trên kết quả truy xuất, các địa điểm trên phù hợp với nhu cầu của bạn. "
            "Nếu muốn đi nhẹ nhàng và tiết kiệm, nên ưu tiên các điểm có ngân sách free và mức đi bộ easy. "
            "Nếu muốn trải nghiệm phong phú hơn, bạn có thể kết hợp thêm các điểm đảo/vịnh "
            "hoặc hoạt động tham quan gần khu vực."
        )

        return "\n".join(lines)
