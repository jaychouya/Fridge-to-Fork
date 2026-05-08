from __future__ import annotations

from src.db.repository import Repository
from src.models.schemas import ExpiringItem, RecipeSuggestion
from src.services.recipe_service import RecipeService


class RecipeRecommender:
    def __init__(self, repo: Repository) -> None:
        self.repo = repo
        self.service = RecipeService()

    def recommend(self, expiring_items: list[ExpiringItem]) -> list[RecipeSuggestion]:
        return self.service.recommend(
            expiring_items=expiring_items,
            repo_cache_get=self.repo.cache_get,
            repo_cache_set=self.repo.cache_set,
        )
