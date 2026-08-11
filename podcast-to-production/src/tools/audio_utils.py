"""Audio processing utilities: concatenation, mixing, loudness."""

import os
from typing import List, Optional

import numpy as np
import soundfile as sf


def read_audio(path: str) -> Optional[tuple]:
    """Read an audio file as (mono float32 samples, sample rate)."""
    if not path or not os.path.exists(path):
        return None
    data, rate = sf.read(path, dtype="float32", always_2d=True)
    return data.mean(axis=1), rate


def concatenate(paths: List[str], output_path: str, gap_seconds: float = 0.35) -> Optional[str]:
    """Concatenate speech clips with a short pause between them."""
    chunks = []
    rate = None
    for path in paths:
        result = read_audio(path)
        if result is None:
            continue
        samples, sr = result
        rate = rate or sr
        if sr != rate:
            samples = _resample(samples, sr, rate)
        chunks.append(samples)
        chunks.append(np.zeros(int(rate * gap_seconds), dtype="float32"))

    if not chunks or rate is None:
        return None

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    sf.write(output_path, np.concatenate(chunks), rate)
    return output_path


def mix_with_music(
    speech_path: str,
    music_path: str,
    output_path: str,
    music_gain_db: float = -18.0,
) -> Optional[str]:
    """Duck background music under the dialogue track and mix."""
    speech = read_audio(speech_path)
    music = read_audio(music_path)
    if speech is None:
        return None
    speech_samples, rate = speech
    if music is None:
        return speech_path

    music_samples, music_rate = music
    if music_rate != rate:
        music_samples = _resample(music_samples, music_rate, rate)

    music_samples = _loop_to_length(music_samples, len(speech_samples))
    gain = 10 ** (music_gain_db / 20.0)
    mixed = speech_samples + music_samples * gain
    peak = float(np.max(np.abs(mixed))) or 1.0
    if peak > 1.0:
        mixed = mixed / peak * 0.98

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    sf.write(output_path, mixed, rate)
    return output_path


def duration_seconds(path: str) -> float:
    result = read_audio(path)
    if result is None:
        return 0.0
    samples, rate = result
    return round(len(samples) / rate, 2)


def _loop_to_length(samples: np.ndarray, length: int) -> np.ndarray:
    if len(samples) == 0:
        return np.zeros(length, dtype="float32")
    repeats = int(np.ceil(length / len(samples)))
    return np.tile(samples, repeats)[:length]


def _resample(samples: np.ndarray, src_rate: int, dst_rate: int) -> np.ndarray:
    if src_rate == dst_rate:
        return samples
    new_length = int(len(samples) * dst_rate / src_rate)
    return np.interp(
        np.linspace(0, len(samples), new_length, endpoint=False),
        np.arange(len(samples)),
        samples,
    ).astype("float32")
