from __future__ import annotations

import json
from pathlib import Path


class NormalizationService:
    def __init__(self, synonyms_path: str = "src/config/synonyms.json") -> None:
        self.synonyms_path = Path(synonyms_path)
        self.synonyms = self._load_synonyms()

    def _load_synonyms(self) -> dict[str, str]:
        if not self.synonyms_path.exists():
            return {}
        return json.loads(self.synonyms_path.read_text(encoding="utf-8"))

    def normalize(self, raw_name: str) -> str:
        key = raw_name.strip().lower()
        return self.synonyms.get(key, key)
