"""Lyria 3 background music generation via Google Cloud."""

import base64
import hashlib
import os
from typing import Optional

import requests

from src.config import Config
from src.tools.ai_gateway import synthesize_music_bed

LYRIA_MODEL = os.getenv("LYRIA_MODEL", "lyria-003")

MOOD_PROMPTS = {
    "happy": "warm upbeat acoustic podcast bed, light percussion",
    "excited": "energetic electronic podcast intro bed, driving pulse",
    "sad": "melancholic solo piano, sparse and reflective",
    "angry": "tense low percussion, urgent strings",
    "calm": "ambient pads, gentle and unobtrusive",
    "nervous": "sparse suspenseful pulse, muted plucks",
    "funny": "playful ukulele and handclaps",
    "serious": "documentary strings, restrained and steady",
    "neutral": "soft lo-fi instrumental bed",
}


class LyriaMusicTool:
    """Generate background music using Lyria 3."""

    def __init__(self, output_dir: Optional[str] = None):
        self.api_key = os.getenv("LYRIA_API_KEY")
        self.project_id = Config.PROJECT_ID
        self.location = Config.LOCATION
        self.output_dir = output_dir or Config.OUTPUT_DIR
        self.base_url = (
            f"https://{self.location}-aiplatform.googleapis.com/v1/projects/"
            f"{self.project_id}/locations/{self.location}/publishers/google/"
            f"models/{LYRIA_MODEL}:predict"
        )

    def generate_music(
        self, mood: str = "calm", duration_seconds: int = 30
    ) -> Optional[str]:
        """Generate background music matching the mood."""
        if not self.api_key:
            print("Lyria key missing - rendering local instrumental bed")
            try:
                return synthesize_music_bed(
                    mood,
                    duration_seconds,
                    os.path.join(self.output_dir, f"music_{mood}_{duration_seconds}s.wav"),
                )
            except Exception as exc:  # noqa: BLE001
                print(f"Music fallback error: {exc}")
                return None

        prompt = MOOD_PROMPTS.get(mood, MOOD_PROMPTS["neutral"])
        try:
            response = requests.post(
                self.base_url,
                json={
                    "instances": [
                        {
                            "prompt": (
                                f"{prompt}; podcast background bed, "
                                f"approximately {duration_seconds} seconds, "
                                "no vocals, loopable"
                            ),
                            "negative_prompt": "vocals, lyrics, sudden transitions",
                        }
                    ],
                    "parameters": {"sample_count": 1},
                },
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=180,
            )

            if response.status_code != 200:
                print(f"Lyria error [{response.status_code}]: {response.text[:500]}")
                return None

            payload = response.json()
            prediction = (payload.get("predictions") or [{}])[0]
            encoded = prediction.get("bytesBase64Encoded") or prediction.get("audio")
            if not encoded:
                print("Lyria error: no audio returned")
                return None

            digest = hashlib.sha1(f"{mood}{duration_seconds}".encode()).hexdigest()[:12]
            os.makedirs(self.output_dir, exist_ok=True)
            output_path = os.path.join(self.output_dir, f"music_{digest}.wav")
            with open(output_path, "wb") as handle:
                handle.write(base64.b64decode(encoded))
            return output_path
        except Exception as exc:  # noqa: BLE001
            print(f"Lyria error: {exc}")
            return None
