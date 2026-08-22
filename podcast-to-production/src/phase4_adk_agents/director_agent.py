"""Director agent: analyses script structure, tone, and production needs."""

from typing import Dict

try:  # pragma: no cover - optional dependency
    from vertexai.preview import reasoning_engines
except ImportError:  # pragma: no cover
    reasoning_engines = None

from src.tools import ai_gateway

from .base_agent import BaseAgent


class DirectorAgent(BaseAgent):
    """Analyzes script structure, tone, and production requirements."""

    SYSTEM_INSTRUCTION = """
    You are a Podcast Director AI. Your role is to analyze podcast scripts and
    prepare them for production.

    TASKS:
    1. Analyze script structure (intro, segments, outro)
    2. Identify speaker roles and their speaking patterns
    3. Determine overall tone and mood
    4. Suggest pacing and emphasis for different sections
    5. Identify production cues (music, sound effects, pauses)

    OUTPUT FORMAT:
    Return a JSON with:
    - structure: dict with sections
    - speakers: list with speaking style notes
    - tone: string describing overall mood
    - pacing: recommendations for each section
    - production_notes: list of cues
    """

    def create_agent(self) -> "reasoning_engines.ReasoningEngine":
        return reasoning_engines.ReasoningEngine.from_config({
            "model": self.model_name,
            "system_instruction": self.SYSTEM_INSTRUCTION,
            "tools": [self._analyze_structure],
        })

    def run(self, script_data: Dict) -> Dict:
        """Run director analysis on script data."""
        payload = {
            "script_text": script_data.get("full_text", ""),
            "speakers": script_data.get("speakers", []),
            "dialogue_segments": script_data.get("dialogue_segments", []),
            "mood": script_data.get("mood", "neutral"),
            "estimated_duration": script_data.get("estimated_duration", 30),
        }
        try:
            if not self.vertex_ready:
                raise RuntimeError("Vertex AI Agent Engine not configured")
            agent = self.create_agent()
            return agent.run(payload)
        except Exception as exc:  # noqa: BLE001 - degrade to gateway/local analysis
            local = self._analyze_structure(script_data)
            if ai_gateway.available():
                try:
                    llm = ai_gateway.chat_json(
                        "Analyze this podcast script for production.\n"
                        f"Speakers: {payload['speakers']}\n"
                        f"Script:\n{payload['script_text'][:6000]}\n\n"
                        "Return JSON with keys: structure (object with intro, "
                        "segments, outro), speakers (list of objects with name and "
                        "speaking_style), tone (string), pacing (object per "
                        "section), production_notes (list of cues).",
                        system=self.SYSTEM_INSTRUCTION,
                    )
                    local.update(llm)
                    local["engine"] = "lovable-ai-gateway"
                    return local
                except Exception as gw_exc:  # noqa: BLE001
                    local["gateway_error"] = str(gw_exc)
            local.update({
                "tone": script_data.get("mood", "neutral"),
                "fallback": True,
                "error": str(exc),
            })
            return local

    def _analyze_structure(self, script_data: Dict) -> Dict:
        """Tool function for analyzing script structure."""
        segments = script_data.get("dialogue_segments", [])
        total_words = len(script_data.get("full_text", "").split())

        return {
            "segments": len(segments),
            "speakers": sorted(
                {s.get("speaker") for s in segments if s.get("speaker")}
            ),
            "total_words": total_words,
            "estimated_podcast_duration_minutes": round(total_words / 150, 1),
            "topics": script_data.get("topics", []),
        }
