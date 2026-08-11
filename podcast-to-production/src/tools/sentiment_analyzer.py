"""Multimodal sentiment analysis using Gemini."""

import json
import os
from typing import Dict, Optional

from google import genai
from google.genai import types

from src.config import Config


class SentimentAnalyzerTool:
    """Analyze sentiment of script text and of the delivered audio."""

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=api_key) if api_key else None
        self.model = Config.GEMINI_MODEL

    def _parse_json(self, text: str) -> Optional[Dict]:
        cleaned = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```")
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return None

    def analyze_sentiment(self, script_text: str) -> Dict:
        """Analyze tone and sentiment of script."""
        if not self.client:
            return {"error": "GEMINI_API_KEY not configured"}
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=f"""
                Analyze the sentiment and tone of this podcast script:
                {script_text[:5000]}

                Return JSON with:
                - overall_tone: (positive/neutral/negative)
                - emotional_arc: list of emotions throughout
                - speaker_tone: dict of speaker to tone
                - audience_engagement: rating 1-10
                - recommendations: list of suggestions
                """,
            )
            parsed = self._parse_json(response.text or "")
            if parsed:
                return parsed
            return {"analysis": response.text, "parsed": False}
        except Exception as exc:  # noqa: BLE001
            print(f"Sentiment error: {exc}")
            return {"error": str(exc)}

    def compare_script_to_audio(self, script_text: str, audio_path: str) -> Dict:
        """Multimodal check: does the delivered audio match the script's tone?"""
        if not self.client:
            return {"error": "GEMINI_API_KEY not configured"}
        if not audio_path or not os.path.exists(audio_path):
            return {"error": "audio file not found", "audio_path": audio_path}
        try:
            with open(audio_path, "rb") as handle:
                audio_bytes = handle.read()

            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav"),
                    f"""
                    Compare the emotional delivery in this audio against the
                    intended tone of the script below.

                    SCRIPT:
                    {script_text[:4000]}

                    Return JSON with:
                    - script_tone
                    - delivered_tone
                    - alignment_score (0-100)
                    - mismatches: list
                    - fixes: list of re-record or re-prompt suggestions
                    """,
                ],
            )
            parsed = self._parse_json(response.text or "")
            return parsed or {"analysis": response.text, "parsed": False}
        except Exception as exc:  # noqa: BLE001
            print(f"Multimodal sentiment error: {exc}")
            return {"error": str(exc)}
