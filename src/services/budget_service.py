from __future__ import annotations

import json
from datetime import date
from pathlib import Path


class BudgetService:
    def __init__(self, budget_usd: float, path: str = "data/api_budget.json") -> None:
        self.budget_usd = budget_usd
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _load(self) -> dict:
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _save(self, payload: dict) -> None:
        self.path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def can_call_external(self) -> bool:
        payload = self._load()
        today = date.today().isoformat()
        spent = float(payload.get(today, 0))
        return spent < self.budget_usd

    def add_cost(self, amount_usd: float) -> None:
        payload = self._load()
        today = date.today().isoformat()
        payload[today] = float(payload.get(today, 0)) + amount_usd
        self._save(payload)
