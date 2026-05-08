from __future__ import annotations

from datetime import datetime

from src.config.settings import settings
from src.db.repository import Repository
from src.models.schemas import VisionIngredient, VisionResult
from src.services.normalization_service import NormalizationService
from src.tools.image_utils import load_and_compress_image, perceptual_hash
from src.tools.openai_vision import detect_ingredients


class VisionSpecialist:
    def __init__(self, repo: Repository, normalizer: NormalizationService) -> None:
        self.repo = repo
        self.normalizer = normalizer

    def analyze(self, image_path: str) -> VisionResult:
        image_hash = perceptual_hash(image_path)
        cached = self.repo.get_image_cache(image_hash)
        if cached:
            return VisionResult(**cached)

        image_bytes = load_and_compress_image(
            image_path=image_path,
            max_edge=settings.image_max_edge,
            quality=settings.image_jpeg_quality,
        )
        result = detect_ingredients(image_bytes=image_bytes, api_key=settings.openai_api_key)
        normalized: list[VisionIngredient] = []
        for item in result.ingredients:
            normalized.append(
                VisionIngredient(
                    name_raw=item.name_raw,
                    name_norm=self.normalizer.normalize(item.name_norm or item.name_raw),
                    quantity_est=item.quantity_est,
                    unit=item.unit,
                    confidence=item.confidence,
                )
            )

        final = VisionResult(
            image_hash=image_hash,
            ingredients=normalized,
            model=result.model,
            created_at=datetime.utcnow(),
        )
        self.repo.set_image_cache(image_hash, final.model_dump(mode="json"))
        return final
