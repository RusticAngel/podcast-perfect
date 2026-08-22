"""Lovable AI Gateway client.

Used as the live model backend when Google Cloud / Vertex AI credentials are
not configured. Provides Gemini chat completions and Gemini text-to-speech.
"""

import base64
import hashlib
import json
import os
import wave
from typing import Dict, List, Optional

import numpy as np
import requests

BASE_URL = "https://ai.gateway.lovable.dev/v1"
CHAT_MODEL = os.getenv("GATEWAY_CHAT_MODEL", "google/gemini-2.5-flash")
TTS_MODEL = os.getenv("GATEWAY_TTS_MODEL", "google/gemini-2.5-flash-tts")


def api_key() -> Optional[str]:
    return os.getenv("LOVABLE_API_KEY")


def available() -> bool:
    return bool(api_key())


def _headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key()}",
        "Content-Type": "application/json",
    }


def chat(prompt: str, system: Optional[str] = None, as_json: bool = False) -> str:
    """Run a chat completion through the gateway."""
    messages: List[Dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload: Dict = {"model": CHAT_MODEL, "messages": messages}
    if as_json:
        payload["response_format"] = {"type": "json_object"}

    response = requests.post(
        f"{BASE_URL}/chat/completions", headers=_headers(), json=payload, timeout=180
    )
    if response.status_code != 200:
        raise RuntimeError(f"gateway chat {response.status_code}: {response.text[:300]}")
    return response.json()["choices"][0]["message"]["content"]


def chat_json(prompt: str, system: Optional[str] = None) -> Dict:
    """Chat completion that returns parsed JSON."""
    raw = chat(prompt, system=system, as_json=True)
    cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```")
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        return {"analysis": raw, "parsed": False}
    return parsed if isinstance(parsed, dict) else {"result": parsed}


def text_to_speech(text: str, voice: str = "Kore", output_path: str = "") -> str:
    """Generate a WAV file for the given text using Gemini TTS."""
    payload = {
        "model": TTS_MODEL,
        "contents": [{"role": "user", "parts": [{"text": text}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}
            },
        },
    }
    response = requests.post(
        f"{BASE_URL}/audio/speech", headers=_headers(), json=payload, timeout=300
    )
    if response.status_code != 200:
        raise RuntimeError(f"gateway tts {response.status_code}: {response.text[:300]}")

    body = response.content
    if not output_path:
        digest = hashlib.sha1(f"{voice}:{text}".encode()).hexdigest()[:12]
        output_path = f"./outputs/speech_{digest}.wav"
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    if body[:4] == b"RIFF":
        with open(output_path, "wb") as handle:
            handle.write(body)
        return output_path

    # Some responses come back as base64 PCM in JSON.
    data = response.json()
    encoded = (
        data.get("audio")
        or data.get("data")
        or data["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]
    )
    pcm = base64.b64decode(encoded)
    with wave.open(output_path, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(24000)
        wav.writeframes(pcm)
    return output_path


MOOD_CHORDS = {
    "happy": [261.63, 329.63, 392.00, 493.88],
    "excited": [293.66, 369.99, 440.00, 587.33],
    "calm": [220.00, 261.63, 329.63, 392.00],
    "serious": [196.00, 233.08, 293.66, 349.23],
    "sad": [174.61, 207.65, 261.63, 311.13],
    "neutral": [220.00, 277.18, 329.63, 415.30],
}


def synthesize_music_bed(
    mood: str = "neutral", duration_seconds: int = 30, output_path: str = ""
) -> str:
    """Render a soft instrumental bed locally (used when Lyria is unavailable)."""
    import soundfile as sf

    rate = 24000
    chord = MOOD_CHORDS.get(mood, MOOD_CHORDS["neutral"])
    t = np.linspace(0, duration_seconds, rate * duration_seconds, endpoint=False)
    bed = np.zeros_like(t)
    for index, freq in enumerate(chord):
        lfo = 0.5 + 0.5 * np.sin(2 * np.pi * (0.05 + 0.01 * index) * t)
        bed += np.sin(2 * np.pi * freq * t) * lfo / (index + 2)
    # gentle pulse + fades
    bed *= 0.6 + 0.4 * np.sin(2 * np.pi * 0.5 * t) ** 2
    fade = int(rate * 1.5)
    bed[:fade] *= np.linspace(0, 1, fade)
    bed[-fade:] *= np.linspace(1, 0, fade)
    bed = (bed / (np.max(np.abs(bed)) or 1.0) * 0.35).astype("float32")

    if not output_path:
        digest = hashlib.sha1(f"{mood}{duration_seconds}".encode()).hexdigest()[:12]
        output_path = f"./outputs/music_{digest}.wav"
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    sf.write(output_path, bed, rate)
    return output_path
