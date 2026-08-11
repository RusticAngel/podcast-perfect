"""Parallel Search API wrapper (partner integration)."""

import os
from typing import Dict, List, Optional

try:  # pragma: no cover - optional dependency at import time
    from parallel_web import ParallelSearch
except ImportError:  # pragma: no cover
    ParallelSearch = None


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

    def search_podcast_data(self, topic: str, genre: Optional[str] = None) -> List[Dict]:
        """Search for podcast industry data."""
        query = (
            f"best {genre or ''} podcasts about {topic} audience engagement trends"
        ).replace("  ", " ")
        return self._search(query)

    def search_competitor_analysis(self, podcast_title: str) -> List[Dict]:
        """Research similar podcasts."""
        query = f"{podcast_title} podcast review ratings audience size"
        return self._search(query)

    def _search(self, query: str, max_results: int = 10) -> List[Dict]:
        """Execute search and return structured results."""
        if not self.client:
            return [{"error": "Parallel API key not configured", "query": query}]

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
