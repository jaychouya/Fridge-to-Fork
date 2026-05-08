from __future__ import annotations

from datetime import date, datetime, timedelta

from src.db.repository import Repository
from src.models.schemas import ExpiringItem, VisionIngredient


class InventoryService:
    def __init__(self, repo: Repository) -> None:
        self.repo = repo

    def ingest_vision_items(self, items: list[VisionIngredient], min_confidence: float = 0.0) -> list[int]:
        lot_ids: list[int] = []
        for item in items:
            if item.confidence < min_confidence:
                continue
            ingredient_id = self.repo.upsert_item(item.name_norm, item.name_norm)
            shelf_days = self.repo.get_shelf_life_days(ingredient_id)
            expires_on = (
                (date.today() + timedelta(days=shelf_days)).isoformat() if shelf_days is not None else None
            )
            lot_id = self.repo.add_lot(
                ingredient_id=ingredient_id,
                quantity=item.quantity_est,
                unit=item.unit,
                source="vision",
                acquired_at=datetime.utcnow().isoformat(),
                expires_on=expires_on,
                confidence=item.confidence,
            )
            self.repo.add_event(
                event_type="add",
                ingredient_id=ingredient_id,
                lot_id=lot_id,
                quantity_delta=item.quantity_est,
                reason="vision_scan",
            )
            lot_ids.append(lot_id)
        return lot_ids

    def get_inventory(self) -> list[dict]:
        return self.repo.list_inventory_view()

    def get_expiring_items(self, within_days: int, limit: int) -> list[ExpiringItem]:
        today = date.today()
        result: list[ExpiringItem] = []
        for row in self.repo.list_inventory_view():
            expiry = row["earliest_expires_on"]
            days_left = None
            if expiry:
                d = date.fromisoformat(expiry)
                days_left = (d - today).days
                if days_left > within_days:
                    continue
            result.append(
                ExpiringItem(
                    ingredient_id=int(row["ingredient_id"]),
                    display_name=str(row["display_name"]),
                    total_quantity=float(row["total_quantity"]),
                    unit=str(row["unit"]),
                    earliest_expires_on=date.fromisoformat(expiry) if expiry else None,
                    days_left=days_left,
                )
            )
        result.sort(key=lambda x: x.days_left if x.days_left is not None else 99999)
        return result[:limit]

    def consume(self, canonical_name: str, quantity: float, reason: str = "cooked") -> float:
        item = self.repo.get_item_by_name(canonical_name)
        if not item:
            return quantity
        return self.repo.consume_inventory(int(item["ingredient_id"]), quantity, reason=reason)
