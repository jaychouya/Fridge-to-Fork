from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class VisionIngredient(BaseModel):
    name_raw: str
    name_norm: str
    quantity_est: float = Field(ge=0)
    unit: str = "item"
    confidence: float = Field(ge=0, le=1)


class VisionResult(BaseModel):
    image_hash: str
    ingredients: list[VisionIngredient]
    model: str
    created_at: datetime


class InventoryLot(BaseModel):
    lot_id: int
    ingredient_id: int
    display_name: str
    quantity: float = Field(ge=0)
    unit: str
    source: Literal["vision", "manual", "adjustment"]
    acquired_at: datetime
    expires_on: Optional[date] = None
    confidence: Optional[float] = None


class InventoryEvent(BaseModel):
    event_id: int
    event_type: Literal["add", "consume", "adjust"]
    ingredient_id: int
    lot_id: Optional[int] = None
    quantity_delta: float
    reason: Optional[str] = None
    created_at: datetime


class ExpiringItem(BaseModel):
    ingredient_id: int
    display_name: str
    total_quantity: float
    unit: str
    earliest_expires_on: Optional[date]
    days_left: Optional[int]


class RecipeSuggestion(BaseModel):
    recipe_id: str
    title: str
    url: str
    matched_ingredients: list[str]
    missing_ingredients: list[str]
    cook_time_minutes: Optional[int] = None
    complexity: Literal["easy", "medium", "hard"] = "medium"
    score: float
    why_recommended: str
