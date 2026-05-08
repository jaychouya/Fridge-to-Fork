from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    tavily_api_key: str = os.getenv("TAVILY_API_KEY", "")
    daily_api_budget_usd: float = float(os.getenv("DAILY_API_BUDGET_USD", "1.5"))
    expiring_days_threshold: int = int(os.getenv("EXPIRING_DAYS_THRESHOLD", "3"))
    top_expire_items: int = int(os.getenv("TOP_EXPIRE_ITEMS", "5"))
    image_max_edge: int = int(os.getenv("IMAGE_MAX_EDGE", "1024"))
    image_jpeg_quality: int = int(os.getenv("IMAGE_JPEG_QUALITY", "80"))
    db_path: str = os.getenv("SQLITE_PATH", "data/fridge.db")


settings = Settings()
