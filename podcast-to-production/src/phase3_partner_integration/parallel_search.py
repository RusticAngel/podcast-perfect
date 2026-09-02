"""Parallel Search API wrapper (partner integration).

Talks to the Parallel Search REST API (`/v1beta/search`) so agents are grounded
in real web results. The optional `parallel_web` SDK is still honoured when a
client is injected (used by the tests).
"""

import os
from typing import Dict, List, Optional

import requests

try:  # pragma: no cover - optional dependency at import time
    from parallel_web import ParallelSearch
except ImportError:  # pragma: no cover
    ParallelSearch = None

API_URL = "https://api.parallel.ai/v1beta/search"


class ParallelResearchTool:
    """Ground agents in real-time web data using Parallel Search."""

    def __init__(self, api_key: Optional[str] = None):
        # Parallel is free for OpenCode agents
        self.api_key = api_key or os.getenv("PARALLEL_API_KEY")
        self.client = (
            ParallelSearch(api_key=self.api_key)
            if self.api_key and ParallelSearch is not None
            else None
        )

    def configured(self) -> bool:
        return bool(self.api_key)

    def search_podcast_data(self, topic: str, genre: Optional[str] = None) -> List[Dict]:
        """Search for podcast industry data."""
        query = (
            f"best {genre or ''} podcasts about {topic} audience engagement trends"
        ).replace("  ", " ")
        return self._search(
            query,
            objective=(
                f"Find real, named podcasts about {topic}"
                f"{f' in the {genre} genre' if genre else ''}, with their format, "
                "episode length, audience size and why listeners like them."
            ),
        )

    def search_competitor_analysis(self, podcast_title: str) -> List[Dict]:
        """Research similar podcasts."""
        query = f"{podcast_title} podcast review ratings audience size"
        return self._search(
            query,
            objective=f"Find reviews, ratings and audience data for the podcast {podcast_title}.",
        )

    def _search(
        self, query: str, max_results: int = 10, objective: Optional[str] = None
    ) -> List[Dict]:
        """Execute search and return structured results."""
        if not self.api_key:
            return [{"error": "Parallel API key not configured", "query": query}]

        if self.client is not None:
            return self._search_sdk(query, max_results)
        return self._search_rest(query, max_results, objective or query)

    def _search_sdk(self, query: str, max_results: int) -> List[Dict]:
        try:
            response = self.client.search(query=query, max_results=max_results)
            results = (
                response.get("results", [])
                if isinstance(response, dict)
                else getattr(response, "results", [])
            )
            return [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "snippet": r.get("snippet", ""),
                    "published_date": r.get("published_date", ""),
                }
                for r in results
            ]
        except Exception as exc:  # noqa: BLE001
            return [{"error": str(exc), "query": query}]

    def _search_rest(self, query: str, max_results: int, objective: str) -> List[Dict]:
        try:
            response = requests.post(
                API_URL,
                headers={"x-api-key": self.api_key, "Content-Type": "application/json"},
                json={
                    "objective": objective,
                    "search_queries": [query],
                    "processor": "base",
                    "max_results": max_results,
                    "max_chars_per_result": 1200,
                },
                timeout=60,
            )
            if response.status_code != 200:
                return [
                    {
                        "error": f"parallel search {response.status_code}: {response.text[:200]}",
                        "query": query,
                    }
                ]
            payload = response.json()
        except Exception as exc:  # noqa: BLE001
            return [{"error": str(exc), "query": query}]

        results = []
        for item in payload.get("results", [])[:max_results]:
            excerpts = item.get("excerpts") or []
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "snippet": " ".join(e.strip() for e in excerpts)[:1200],
                "published_date": item.get("published_date", "")
                or item.get("date", ""),
                "query": query,
            })
        return results
