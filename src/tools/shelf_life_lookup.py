from __future__ import annotations

import requests


LOCAL_RULES: dict[str, int] = {
    "egg": 21,
    "milk": 7,
    "tomato": 7,
    "potato": 30,
    "onion": 30,
    "carrot": 14,
    "chicken": 2,
    "beef": 3,
    "spinach": 5,
}


def get_local_shelf_life_days(ingredient: str) -> int | None:
    return LOCAL_RULES.get(ingredient.lower())


def fetch_remote_shelf_life_days(ingredient: str, timeout: int = 8) -> int | None:
    query = ingredient.strip().replace(" ", "+")
    url = f"https://www.stilltasty.com/fooditems/index/{query}"
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code != 200:
            return None
        text = response.text.lower()
        if "3-5 days" in text:
            return 5
        if "1-2 weeks" in text:
            return 14
        if "2-3 days" in text:
            return 3
        return None
    except requests.RequestException:
        return None
