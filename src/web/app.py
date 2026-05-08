from __future__ import annotations

import base64
import tempfile
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from starlette.requests import Request

from src.agents.inventory_tracker import InventoryTracker
from src.agents.meal_planner import MealPlanner
from src.agents.recipe_recommender import RecipeRecommender
from src.app_context import build_orchestrator, build_repo
from src.config.settings import settings
from src.services.budget_service import BudgetService

app = FastAPI(title="Fridge-to-Fork")
base_dir = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(base_dir / "static")), name="static")


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self'; "
        "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; "
        "base-uri 'self'; form-action 'self'; object-src 'none'"
    )
    return response


class CookedRequest(BaseModel):
    ingredient: str
    quantity: float


class ScanRequest(BaseModel):
    image_base64: str
    filename: str = "upload.jpg"


@app.get("/")
def index():
    return FileResponse(base_dir / "templates" / "index.html")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/inventory")
def inventory():
    repo = build_repo()
    tracker = InventoryTracker(repo)
    return {"items": tracker.view()}


@app.get("/api/recommend")
def recommend():
    repo = build_repo()
    tracker = InventoryTracker(repo)
    recommender = RecipeRecommender(repo)
    planner = MealPlanner()
    expiring = tracker.expiring(settings.expiring_days_threshold, settings.top_expire_items)
    recipes = recommender.recommend(expiring)
    return {
        "expiring": [e.model_dump(mode="json") for e in expiring],
        "recipes": [r.model_dump(mode="json") for r in recipes],
        "message": planner.daily_message(expiring, recipes),
    }


@app.post("/api/cooked")
def cooked(payload: CookedRequest):
    repo = build_repo()
    tracker = InventoryTracker(repo)
    left = tracker.consume(payload.ingredient, payload.quantity, reason="user_cooked")
    return {"leftover": left, "ok": left == 0}


@app.post("/api/scan")
def scan(payload: ScanRequest):
    budget = BudgetService(settings.daily_api_budget_usd)
    if not budget.can_call_external():
        return {"ok": False, "error": "daily budget reached"}

    suffix = Path(payload.filename or "upload.jpg").suffix or ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(base64.b64decode(payload.image_base64))
        tmp_path = tmp.name

    try:
        orchestrator = build_orchestrator()
        result = orchestrator.run_scan_flow(tmp_path)
        budget.add_cost(0.02)
        return {
            "ok": True,
            "ingredients": [x.model_dump(mode="json") for x in result.get("confirmed_ingredients", [])],
            "expiring": [x.model_dump(mode="json") for x in result.get("expiring_items", [])],
            "recipes": [x.model_dump(mode="json") for x in result.get("recipes", [])],
            "message": result.get("reminder", ""),
        }
    finally:
        Path(tmp_path).unlink(missing_ok=True)
