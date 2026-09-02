"""Researcher agent: market intelligence grounded in real Parallel Search results."""

from typing import Dict, List

try:  # pragma: no cover - optional dependency
    from vertexai.preview import reasoning_engines
except ImportError:  # pragma: no cover
    reasoning_engines = None

from src.phase3_partner_integration.parallel_search import ParallelResearchTool
from src.tools import ai_gateway

from .base_agent import BaseAgent


class ResearcherAgent(BaseAgent):
    """Researches the podcast market using the Parallel Search API."""

    SYSTEM_INSTRUCTION = """
    You are a Podcast Research AI. You summarise MARKET DATA THAT IS GIVEN TO YOU.

    HARD RULES:
    - Only reference podcasts, numbers and claims that appear in the supplied
      search results. Never invent a podcast, host, rating or audience figure.
    - Every comparable podcast MUST include the exact source_url it came from,
      copied verbatim from the supplied results.
    - If the results do not support a claim, omit it rather than guessing.

    OUTPUT FORMAT (JSON):
    - market_data: object with findings drawn from the sources
    - comparable_podcasts: list of {title, why_similar, source_url}
    - audience_insights: object with demographics and preferences
    - recommendations: list of actionable suggestions
    """

    def __init__(self, model_name: str = "gemini-2.0-flash-exp"):
        super().__init__(model_name)
        self.parallel_tool = ParallelResearchTool()

    def create_agent(self) -> "reasoning_engines.ReasoningEngine":
        return reasoning_engines.ReasoningEngine.from_config({
            "model": self.model_name,
            "system_instruction": self.SYSTEM_INSTRUCTION,
            "tools": [self._search_podcast_market],
        })

    def run(self, script_data: Dict, director_analysis: Dict) -> Dict:
        """Research the market: real search first, model only summarises sources."""
        params = {
            "topics": director_analysis.get("topics") or script_data.get("topics", []),
            "genre": script_data.get("genre", "general"),
            "mood": script_data.get("mood", "neutral"),
            "estimated_duration": script_data.get("estimated_duration", 30),
        }

        search = self._search_podcast_market(params)
        sources: List[Dict] = search["market_research"]
        result: Dict = dict(search)
        result["source_provider"] = "parallel-search"
        result["grounded"] = bool(sources)

        if not sources:
            result.update({
                "market_data": {},
                "comparable_podcasts": [],
                "audience_insights": {},
                "recommendations": [
                    "Market research unavailable: add a PARALLEL_API_KEY so comparables "
                    "come from real web results instead of model guesses."
                ],
                "search_errors": search.get("search_errors", []),
            })
            return result

        if not ai_gateway.available():
            result.update({
                "market_data": {"note": "Raw Parallel Search results only (no model available)."},
                "comparable_podcasts": [
                    {
                        "title": s.get("title", ""),
                        "why_similar": (s.get("snippet") or "")[:220],
                        "source_url": s.get("url", ""),
                    }
                    for s in sources[:5]
                ],
                "audience_insights": {},
                "recommendations": [],
            })
            return result

        allowed = {s.get("url") for s in sources if s.get("url")}
        formatted = "\n\n".join(
            f"[{i + 1}] {s.get('title', '')}\nURL: {s.get('url', '')}\n"
            f"DATE: {s.get('published_date', '')}\nEXCERPT: {s.get('snippet', '')}"
            for i, s in enumerate(sources)
        )
        try:
            llm = ai_gateway.chat_json(
                "Summarise podcast market intelligence using ONLY the search results below.\n"
                f"Genre: {params['genre']}\nTopics: {params['topics']}\n"
                f"Mood: {params['mood']}\n"
                f"Estimated duration: {params['estimated_duration']} min\n\n"
                f"SEARCH RESULTS:\n{formatted}\n\n"
                "Return JSON with keys: market_data (object), comparable_podcasts "
                "(list of {title, why_similar, source_url} where source_url is one of "
                "the URLs above), audience_insights (object), recommendations (list).",
                system=self.SYSTEM_INSTRUCTION,
            )
        except Exception as exc:  # noqa: BLE001
            result["gateway_error"] = str(exc)
            result["comparable_podcasts"] = [
                {
                    "title": s.get("title", ""),
                    "why_similar": (s.get("snippet") or "")[:220],
                    "source_url": s.get("url", ""),
                }
                for s in sources[:5]
            ]
            return result

        # Drop anything the model produced that is not backed by a retrieved URL.
        verified = [
            c
            for c in llm.get("comparable_podcasts", [])
            if isinstance(c, dict) and c.get("source_url") in allowed
        ]
        dropped = len(llm.get("comparable_podcasts", [])) - len(verified)
        llm["comparable_podcasts"] = verified
        result.update(llm)
        result["engine"] = "parallel-search + lovable-ai-gateway"
        result["unverified_comparables_dropped"] = dropped
        return result

    def _search_podcast_market(self, research_params: Dict) -> Dict:
        """Tool function for searching podcast market data."""
        topics = research_params.get("topics", [])
        genre = research_params.get("genre", "general")

        raw: List[Dict] = []
        for topic in topics[:3]:
            raw.extend(self.parallel_tool.search_podcast_data(topic, genre))
        if not topics:
            raw.extend(self.parallel_tool.search_podcast_data(genre))

        errors = [r.get("error") for r in raw if r.get("error")]
        results, seen = [], set()
        for r in raw:
            url = r.get("url")
            if r.get("error") or not url or url in seen:
                continue
            seen.add(url)
            results.append(r)

        return {
            "market_research": results[:10],
            "similar_podcasts_count": len(results),
            "trending_topics": topics[:5],
            "search_errors": errors,
            "parallel_configured": self.parallel_tool.configured(),
        }
