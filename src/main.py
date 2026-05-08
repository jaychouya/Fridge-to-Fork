from __future__ import annotations

import argparse
import json

from src.agents.inventory_tracker import InventoryTracker
from src.agents.meal_planner import MealPlanner
from src.agents.recipe_recommender import RecipeRecommender
from src.app_context import build_orchestrator
from src.config.settings import settings
from src.db.repository import Repository
from src.services.budget_service import BudgetService


def cmd_scan(args: argparse.Namespace) -> None:
    budget = BudgetService(settings.daily_api_budget_usd)
    if not budget.can_call_external():
        print("今日API预算已达上限，拒绝外部调用。")
        return
    orchestrator = build_orchestrator()
    result = orchestrator.run_scan_flow(args.image)
    budget.add_cost(0.02)
    print(result.get("reminder", ""))


def cmd_inventory(_: argparse.Namespace) -> None:
    repo = Repository(settings.db_path)
    inventory = InventoryTracker(repo=repo)
    print(json.dumps(inventory.view(), ensure_ascii=False, indent=2))


def cmd_recommend(_: argparse.Namespace) -> None:
    repo = Repository(settings.db_path)
    inventory = InventoryTracker(repo=repo)
    recipe = RecipeRecommender(repo=repo)
    planner = MealPlanner()
    expiring = inventory.expiring(settings.expiring_days_threshold, settings.top_expire_items)
    recs = recipe.recommend(expiring)
    print(planner.daily_message(expiring, recs))
    print(json.dumps([r.model_dump(mode="json") for r in recs], ensure_ascii=False, indent=2))


def cmd_cooked(args: argparse.Namespace) -> None:
    repo = Repository(settings.db_path)
    inventory = InventoryTracker(repo=repo)
    leftover = inventory.consume(args.ingredient, args.quantity, reason="user_cooked")
    if leftover > 0:
        print(f"库存不足，仍缺少: {leftover}")
    else:
        print("库存扣减完成")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fridge-to-Fork CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="Analyze fridge image")
    scan.add_argument("--image", required=True)
    scan.set_defaults(func=cmd_scan)

    inv = sub.add_parser("inventory", help="Show inventory")
    inv.set_defaults(func=cmd_inventory)

    rec = sub.add_parser("recommend", help="Recommend recipes")
    rec.set_defaults(func=cmd_recommend)

    cooked = sub.add_parser("cooked", help="Deduct ingredient")
    cooked.add_argument("--ingredient", required=True)
    cooked.add_argument("--quantity", required=True, type=float)
    cooked.set_defaults(func=cmd_cooked)

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
