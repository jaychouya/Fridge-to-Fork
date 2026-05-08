from __future__ import annotations

from hashlib import sha1

from src.config.settings import settings
from src.models.schemas import ExpiringItem, RecipeSuggestion
from src.tools.tavily_recipe_search import search_recipe_candidates


class RecipeService:
    def __init__(self, ttl_seconds: int = 60 * 60 * 12) -> None:
        self.ttl_seconds = ttl_seconds

    def recommend(self, expiring_items: list[ExpiringItem], repo_cache_get, repo_cache_set) -> list[RecipeSuggestion]:
        if not expiring_items:
            return []
        ingredients = [item.display_name for item in expiring_items]
        query = f"recipe using {', '.join(ingredients)}"
        key = "tavily:" + sha1(query.encode("utf-8")).hexdigest()
        cached = repo_cache_get(key)
        results = cached.get("results", []) if cached else []
        if not cached and settings.tavily_api_key:
            results = search_recipe_candidates(query, settings.tavily_api_key, max_results=8)
            repo_cache_set(key, {"results": results}, self.ttl_seconds)

        suggestions: list[RecipeSuggestion] = []
        seen_urls: set[str] = set()
        expiring_names = {x.display_name.lower() for x in expiring_items}
        for idx, row in enumerate(results):
            url = row.get("url", "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            title = row.get("title", "Recipe")
            title_lower = title.lower()
            matched = [n for n in expiring_names if n in title_lower]
            missing = [n for n in expiring_names if n not in title_lower][:3]
            score = len(matched) * 2 - len(missing) * 0.5 + max(0, 3 - idx)
            suggestions.append(
                RecipeSuggestion(
                    recipe_id=f"r{idx+1}",
                    title=title,
                    url=url,
                    matched_ingredients=matched,
                    missing_ingredients=missing,
                    complexity="medium",
                    score=score,
                    why_recommended=f"Matches expiring ingredients: {', '.join(matched) if matched else 'partial match'}",
                )
            )
        suggestions.sort(key=lambda x: x.score, reverse=True)
        return suggestions[:3]
