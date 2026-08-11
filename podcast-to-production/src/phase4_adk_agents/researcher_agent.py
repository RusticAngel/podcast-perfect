"""Researcher agent: market intelligence via Gemini + Parallel Search."""

from typing import Dict

from vertexai.preview import reasoning_engines

from src.phase3_partner_integration.parallel_search import ParallelResearchTool

from .base_agent import BaseAgent


class ResearcherAgent(BaseAgent):
    """Researches podcast market using Parallel Search API."""

    SYSTEM_INSTRUCTION = """
    You are a Podcast Research AI. Your role is to provide market intelligence
    for podcast production.

    TASKS:
    1. Research successful podcasts in similar genres
    2. Identify audience preferences and trends
    3. Find comparable podcast formats and structures
    4. Gather data on episode lengths, release schedules, and engagement
    5. Provide recommendations based on market data

    OUTPUT FORMAT:
    Return a JSON with:
    - market_data: dict with findings
    - comparable_podcasts: list with details
    - audience_insights: dict with demographics and preferences
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
        """Run research based on script content and director analysis."""
        params = {
            "topics": director_analysis.get("topics")
            or script_data.get("topics", []),
            "genre": script_data.get("genre", "general"),
            "mood": script_data.get("mood", "neutral"),
            "estimated_duration": script_data.get("estimated_duration", 30),
        }
        try:
            agent = self.create_agent()
            return agent.run(params)
        except Exception as exc:  # noqa: BLE001 - degrade to raw search
            result = self._search_podcast_market(params)
            result.update({"fallback": True, "error": str(exc)})
            return result

    def _search_podcast_market(self, research_params: Dict) -> Dict:
        """Tool function for searching podcast market data."""
        topics = research_params.get("topics", [])
        genre = research_params.get("genre", "general")

        results = []
        for topic in topics[:3]:
            results.extend(self.parallel_tool.search_podcast_data(topic, genre))

        return {
            "market_research": results[:10],
            "similar_podcasts_count": len(results),
            "trending_topics": topics[:5],
        }
