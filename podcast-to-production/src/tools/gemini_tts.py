"""Gemini TTS wrapper with multi-speaker support."""

import hashlib
import os
import wave
from typing import Dict, List, Optional

try:  # pragma: no cover - optional dependency
    from google import genai
    from google.genai import types
except ImportError:  # pragma: no cover
    genai = None
    types = None

from src.tools import ai_gateway

from src.config import Config

TTS_MODEL = os.getenv("GEMINI_TTS_MODEL", "gemini-2.5-flash-preview-tts")

# Map Google Cloud style voice names to Gemini prebuilt voices.
VOICE_MAP = {
    "en-US-Neural2-F": "Kore",
    "en-US-Neural2-M": "Puck",
}


class GeminiTTSTool:
    """Generate speech using Gemini TTS."""

    def __init__(self, output_dir: Optional[str] = None):
        api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=api_key) if api_key and genai else None
        self.output_dir = output_dir or Config.OUTPUT_DIR

    def _resolve_voice(self, voice: str) -> str:
        return VOICE_MAP.get(voice, voice)

    def _path(self, prefix: str, key: str) -> str:
        digest = hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]
        os.makedirs(self.output_dir, exist_ok=True)
        return os.path.join(self.output_dir, f"{prefix}_{digest}.wav")

    def _write_wav(self, path: str, pcm: bytes, rate: int = 24000) -> str:
        with wave.open(path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(rate)
            wf.writeframes(pcm)
        return path

    def generate_speech(
        self, text: str, voice: str = Config.DEFAULT_VOICE
    ) -> Optional[str]:
        """Generate speech audio from text for a single voice."""
        if not self.client:
            print("TTS error: GEMINI_API_KEY not configured")
            return None
        try:
            response = self.client.models.generate_content(
                model=TTS_MODEL,
                contents=text,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=self._resolve_voice(voice)
                            )
                        )
                    ),
                ),
            )
            pcm = response.candidates[0].content.parts[0].inline_data.data
            return self._write_wav(self._path("speech", f"{voice}:{text}"), pcm)
        except Exception as exc:  # noqa: BLE001
            print(f"TTS error: {exc}")
            return None

    def generate_multi_speaker(
        self, segments: List[Dict], voice_assignment: Dict[str, str]
    ) -> Optional[str]:
        """Generate a single multi-speaker audio track from dialogue segments."""
        if not self.client or not segments:
            return None

        speakers = list(dict.fromkeys(s.get("speaker", "NARRATOR") for s in segments))
        # Gemini multi-speaker TTS supports up to two speakers per request.
        speakers = speakers[:2]
        transcript = "\n".join(
            f"{s.get('speaker', 'NARRATOR')}: {s.get('text', '')}"
            for s in segments
            if s.get("speaker", "NARRATOR") in speakers
        )

        try:
            response = self.client.models.generate_content(
                model=TTS_MODEL,
                contents=f"TTS the following podcast conversation:\n{transcript}",
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                            speaker_voice_configs=[
                                types.SpeakerVoiceConfig(
                                    speaker=speaker,
                                    voice_config=types.VoiceConfig(
                                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                            voice_name=self._resolve_voice(
                                                voice_assignment.get(
                                                    speaker, Config.DEFAULT_VOICE
                                                )
                                            )
                                        )
                                    ),
                                )
                                for speaker in speakers
                            ]
                        )
                    ),
                ),
            )
            pcm = response.candidates[0].content.parts[0].inline_data.data
            return self._write_wav(self._path("episode", transcript), pcm)
        except Exception as exc:  # noqa: BLE001
            print(f"Multi-speaker TTS error: {exc}")
            return None
