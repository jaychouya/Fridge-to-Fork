from __future__ import annotations

import base64
import json
from datetime import datetime

from src.models.schemas import VisionIngredient, VisionResult


def detect_ingredients(image_bytes: bytes, api_key: str, model: str = "gpt-4o") -> VisionResult:
    try:
        from openai import OpenAI
    except ModuleNotFoundError:
        return VisionResult(image_hash="", ingredients=[], model=model, created_at=datetime.utcnow())
    client = OpenAI(api_key=api_key)
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    prompt = (
        "Identify visible fridge ingredients. Return JSON only with key 'ingredients'. "
        "Each item: name_raw, name_norm, quantity_est (float), unit, confidence (0-1). "
        "Use conservative confidence for unclear items."
    )
    response = client.chat.completions.create(
        model=model,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "You are a strict food item detector."},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                ],
            },
        ],
    )
    payload = json.loads(response.choices[0].message.content or "{}")
    ingredients = [VisionIngredient(**x) for x in payload.get("ingredients", [])]
    return VisionResult(
        image_hash="",
        ingredients=ingredients,
        model=model,
        created_at=datetime.utcnow(),
    )
