from __future__ import annotations

from src.db.repository import Repository
from src.models.schemas import ExpiringItem, VisionIngredient
from src.services.inventory_service import InventoryService
from src.services.shelf_life_service import ShelfLifeService


class InventoryTracker:
    def __init__(self, repo: Repository) -> None:
        self.repo = repo
        self.inventory_service = InventoryService(repo)
        self.shelf_life_service = ShelfLifeService(repo)

    def update_from_vision(self, ingredients: list[VisionIngredient]) -> list[int]:
        for item in ingredients:
            ingredient_id = self.repo.upsert_item(item.name_norm, item.name_norm)
            self.shelf_life_service.ensure_rule(ingredient_id, item.name_norm)
        return self.inventory_service.ingest_vision_items(ingredients)

    def expiring(self, within_days: int, limit: int) -> list[ExpiringItem]:
        return self.inventory_service.get_expiring_items(within_days, limit)

    def consume(self, canonical_name: str, quantity: float, reason: str = "cooked") -> float:
        return self.inventory_service.consume(canonical_name, quantity, reason=reason)

    def view(self) -> list[dict]:
        return self.inventory_service.get_inventory()
