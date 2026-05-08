from __future__ import annotations

def search_recipe_candidates(query: str, api_key: str, max_results: int = 5) -> list[dict]:
    try:
        from tavily import TavilyClient
    except ModuleNotFoundError:
        return []
    client = TavilyClient(api_key=api_key)
    result = client.search(
        query=query,
        search_depth="basic",
        include_answer=False,
        include_raw_content=False,
        max_results=max_results,
    )
    return result.get("results", [])
