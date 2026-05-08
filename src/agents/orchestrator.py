from __future__ import annotations

from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from src.agents.inventory_tracker import InventoryTracker
from src.agents.meal_planner import MealPlanner
from src.agents.recipe_recommender import RecipeRecommender
from src.agents.vision_specialist import VisionSpecialist
from src.config.settings import settings
from src.models.schemas import RecipeSuggestion, VisionIngredient


class WorkflowState(TypedDict, total=False):
    image_path: str
    ingredients: list[VisionIngredient]
    confirmed_ingredients: list[VisionIngredient]
    expiring_items: list
    recipes: list[RecipeSuggestion]
    reminder: str


class Orchestrator:
    def __init__(
        self,
        vision: VisionSpecialist,
        inventory: InventoryTracker,
        recipe: RecipeRecommender,
        planner: MealPlanner,
    ) -> None:
        self.vision = vision
        self.inventory = inventory
        self.recipe = recipe
        self.planner = planner
        self.workflow = self._build()

    def _build(self):
        graph = StateGraph(WorkflowState)

        def vision_node(state: WorkflowState) -> WorkflowState:
            result = self.vision.analyze(state["image_path"])
            return {"ingredients": result.ingredients}

        def hitl_confirm_node(state: WorkflowState) -> WorkflowState:
            confirmed: list[VisionIngredient] = []
            for item in state["ingredients"]:
                if item.confidence >= 0.65:
                    confirmed.append(item)
                    continue
                ans = input(f"低置信度食材 {item.name_raw} ({item.confidence:.2f})，是否入库? [y/N]: ").strip().lower()
                if ans == "y":
                    confirmed.append(item)
            return {"confirmed_ingredients": confirmed}

        def inventory_node(state: WorkflowState) -> WorkflowState:
            self.inventory.update_from_vision(state.get("confirmed_ingredients", []))
            expiring = self.inventory.expiring(settings.expiring_days_threshold, settings.top_expire_items)
            return {"expiring_items": expiring}

        def recipe_node(state: WorkflowState) -> WorkflowState:
            recs = self.recipe.recommend(state.get("expiring_items", []))
            return {"recipes": recs}

        def reminder_node(state: WorkflowState) -> WorkflowState:
            msg = self.planner.daily_message(state.get("expiring_items", []), state.get("recipes", []))
            return {"reminder": msg}

        graph.add_node("vision", vision_node)
        graph.add_node("confirm", hitl_confirm_node)
        graph.add_node("inventory", inventory_node)
        graph.add_node("recipe", recipe_node)
        graph.add_node("reminder", reminder_node)

        graph.add_edge(START, "vision")
        graph.add_edge("vision", "confirm")
        graph.add_edge("confirm", "inventory")
        graph.add_edge("inventory", "recipe")
        graph.add_edge("recipe", "reminder")
        graph.add_edge("reminder", END)
        return graph.compile()

    def run_scan_flow(self, image_path: str) -> WorkflowState:
        return self.workflow.invoke({"image_path": image_path})
