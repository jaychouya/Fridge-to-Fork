from __future__ import annotations

from src.db.repository import Repository
from src.tools.shelf_life_lookup import fetch_remote_shelf_life_days, get_local_shelf_life_days


class ShelfLifeService:
    def __init__(self, repo: Repository, ttl_seconds: int = 60 * 60 * 24 * 7) -> None:
        self.repo = repo
        self.ttl_seconds = ttl_seconds

    def ensure_rule(self, ingredient_id: int, canonical_name: str) -> int | None:
        existing = self.repo.get_shelf_life_days(ingredient_id)
        if existing is not None:
            return existing

        key = f"shelf_life:{canonical_name}"
        cached = self.repo.cache_get(key)
        if cached and "days" in cached:
            days = int(cached["days"])
            self.repo.set_shelf_life_rule(ingredient_id, days, source="cache")
            return days

        days = get_local_shelf_life_days(canonical_name)
        source = "local"
        if days is None:
            remote = fetch_remote_shelf_life_days(canonical_name)
            if remote is not None:
                days = remote
                source = "remote"

        if days is None:
            return None

        self.repo.cache_set(key, {"days": days}, self.ttl_seconds)
        self.repo.set_shelf_life_rule(ingredient_id, days, source=source)
        return days
