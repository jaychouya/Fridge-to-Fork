from __future__ import annotations

from src.agents.inventory_tracker import InventoryTracker
from src.agents.meal_planner import MealPlanner
from src.agents.orchestrator import Orchestrator
from src.agents.recipe_recommender import RecipeRecommender
from src.agents.vision_specialist import VisionSpecialist
from src.config.settings import settings
from src.db.repository import Repository
from src.services.normalization_service import NormalizationService


def build_orchestrator() -> Orchestrator:
    repo = Repository(settings.db_path)
    normalizer = NormalizationService()
    vision = VisionSpecialist(repo=repo, normalizer=normalizer)
    inventory = InventoryTracker(repo=repo)
    recipe = RecipeRecommender(repo=repo)
    planner = MealPlanner()
    return Orchestrator(vision=vision, inventory=inventory, recipe=recipe, planner=planner)


def build_repo() -> Repository:
    return Repository(settings.db_path)
