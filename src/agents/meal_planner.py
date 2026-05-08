from __future__ import annotations

from datetime import date

from src.models.schemas import ExpiringItem, RecipeSuggestion


class MealPlanner:
    def daily_message(self, expiring_items: list[ExpiringItem], recipes: list[RecipeSuggestion]) -> str:
        today = date.today().isoformat()
        if not expiring_items:
            return f"[{today}] 库存正常，无临期食材。"
        lines = [f"[{today}] 检测到临期食材："]
        for item in expiring_items:
            left = "unknown" if item.days_left is None else f"{item.days_left}天"
            lines.append(f"- {item.display_name} ({item.total_quantity} {item.unit}, 剩余{left})")
        if recipes:
            lines.append("建议优先烹饪：")
            for rec in recipes:
                lines.append(f"- {rec.title} ({rec.url})")
        return "\n".join(lines)
