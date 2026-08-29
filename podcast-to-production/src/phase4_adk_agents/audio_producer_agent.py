"""Audio producer agent: Gemini TTS + Lyria 3 music + sentiment analysis."""

from typing import Dict, List

try:  # pragma: no cover - optional dependency
    from vertexai.preview import reasoning_engines
except ImportError:  # pragma: no cover
    reasoning_engines = None

from src.config import Config
from src.tools.gemini_tts import GeminiTTSTool
from src.tools.lyria_music import LyriaMusicTool
from src.tools.sentiment_analyzer import SentimentAnalyzerTool

from .base_agent import BaseAgent


class AudioProducerAgent(BaseAgent):
    """Generates audio assets using Gemini TTS and Lyria 3."""

    SYSTEM_INSTRUCTION = """
    You are an Audio Production AI. Your role is to generate high-quality audio
    assets for podcast production.

    TASKS:
    1. Convert script text to speech using Gemini TTS (multi-speaker)
    2. Generate appropriate background music using Lyria 3
    3. Perform sentiment analysis on audio vs. script
    4. Ensure audio quality and timing
    5. Output complete audio files

    OUTPUT FORMAT:
    Return a JSON with:
    - audio_files: dict with paths to generated audio
    - music_files: dict with paths to background music
    - sentiment_analysis: dict with tone comparisons
    - production_notes: dict with timing and quality metrics
    """

    def __init__(self, model_name: str = "gemini-2.0-flash-exp"):
        super().__init__(model_name)
        self.tts_tool = GeminiTTSTool()
        self.music_tool = LyriaMusicTool()
        self.sentiment_tool = SentimentAnalyzerTool()

    def create_agent(self) -> "reasoning_engines.ReasoningEngine":
        return reasoning_engines.ReasoningEngine.from_config({
            "model": self.model_name,
            "system_instruction": self.SYSTEM_INSTRUCTION,
            "tools": [self._produce_audio],
        })

    def run(
        self,
        script_data: Dict,
        director_analysis: Dict,
        music_mood: str = "",
        music_intensity: float = 0.6,
        voice_map: Dict[str, str] | None = None,
    ) -> Dict:
        """Generate audio assets from script and analysis."""
        params = {
            "dialogue_segments": script_data.get("dialogue_segments", []),
            "speakers": script_data.get("speakers", []),
            "tone": director_analysis.get("tone", script_data.get("mood", "neutral")),
            "pacing": director_analysis.get("pacing", {}),
            "structure": director_analysis.get("structure", {}),
            "music_mood": music_mood,
            "music_intensity": music_intensity,
            "voice_map": voice_map or {},
        }
        try:
            if not self.vertex_ready:
                raise RuntimeError("Vertex AI Agent Engine not configured")
            agent = self.create_agent()
            agent.run(params)
        except Exception:  # noqa: BLE001 - tool execution is the source of truth
            pass
        return self._produce_audio(params)

    def _produce_audio(self, production_params: Dict) -> Dict:
        """Tool function for audio production."""
        segments: List[Dict] = production_params.get("dialogue_segments", [])
        speakers: List[str] = production_params.get("speakers", [])
        tone = production_params.get("tone", "neutral")
        voice_map: Dict[str, str] = production_params.get("voice_map") or {}

        audio_files = []
        for segment in segments:
            speaker = segment.get("speaker", "Narrator")
            text = segment.get("text", "")
            if not text:
                continue
            voice = voice_map.get(speaker) or self._assign_voice(speaker, speakers)
            audio_path = self.tts_tool.generate_speech(text, voice)
            audio_files.append({
                "speaker": speaker,
                "text": text,
                "audio_path": audio_path,
                "voice": voice,
            })

        requested_mood = (production_params.get("music_mood") or "").strip().lower()
        mood = requested_mood if requested_mood and requested_mood != "auto" else (
            self._normalize_mood(tone)
        )
        intensity = float(production_params.get("music_intensity", 0.6) or 0.6)
        music_path = self.music_tool.generate_music(
            mood, duration_seconds=30, intensity=intensity
        )

        sentiment = self.sentiment_tool.analyze_sentiment(
            script_text=" ".join(s.get("text", "") for s in segments)
        )

        return {
            "audio_files": audio_files,
            "music_path": music_path,
            "music_mood": mood,
            "music_intensity": intensity,
            "sentiment_analysis": sentiment,
            "total_segments": len(segments),
        }

    @staticmethod
    def _normalize_mood(tone: str) -> str:
        """Map a free-form tone description onto a supported music mood."""
        from src.tools.lyria_music import MOOD_PROMPTS

        text = (tone or "").lower()
        for mood in MOOD_PROMPTS:
            if mood in text:
                return mood
        keywords = {
            "informative": "serious",
            "enthusiastic": "excited",
            "optimistic": "happy",
            "reflective": "calm",
            "tense": "nervous",
        }
        for keyword, mood in keywords.items():
            if keyword in text:
                return mood
        return "neutral"

    def _assign_voice(self, speaker: str, speakers: List[str]) -> str:
        """Assign TTS voice based on speaker role."""
        if speaker in speakers and len(speakers) > 1:
            index = sorted(speakers).index(speaker)
            return Config.DEFAULT_VOICE if index % 2 == 0 else Config.SECONDARY_VOICE
        return Config.DEFAULT_VOICE
