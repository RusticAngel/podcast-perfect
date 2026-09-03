"""Render a video-podcast (talking heads) MP4 from the produced episode audio.

The renderer draws a studio stage with one card per speaker, highlights whoever
is talking, and animates each card's level meter from the real audio envelope.
Frames are drawn with Pillow and muxed with the final mix by ffmpeg.
"""

from __future__ import annotations

import math
import os
import shutil
import subprocess
import tempfile
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from src.tools import audio_utils

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
]

# Studio console palette (matches the web UI).
BG_TOP = (14, 17, 24)
BG_BOTTOM = (24, 29, 40)
CARD_IDLE = (30, 36, 48)
CARD_ACTIVE = (44, 54, 74)
TEXT = (236, 240, 247)
MUTED = (140, 150, 168)
ACCENT_CYCLE = [
    (255, 138, 76),
    (86, 190, 255),
    (150, 220, 140),
    (226, 140, 240),
    (255, 205, 100),
    (128, 168, 255),
]


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def _font(size: int) -> ImageFont.FreeTypeFont:
    for path in FONT_CANDIDATES:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    try:  # fontconfig-provided fonts (Nix sandboxes)
        import subprocess as _sp

        out = _sp.run(
            ["fc-match", "-f", "%{file}", "DejaVu Sans:bold"],
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()
        if out and os.path.exists(out):
            return ImageFont.truetype(out, size)
    except Exception:  # noqa: BLE001
        pass
    return ImageFont.load_default()


def build_timeline(
    audio_files: Sequence[Dict], gap_seconds: float = 0.35
) -> List[Dict[str, object]]:
    """Convert produced speech clips into (speaker, start, end) spans.

    Mirrors ``audio_utils.concatenate`` so the video stays in sync with the mix.
    """
    timeline: List[Dict[str, object]] = []
    cursor = 0.0
    for item in audio_files:
        path = item.get("audio_path")
        if not path or not os.path.exists(path):
            continue
        duration = audio_utils.duration_seconds(path) or 0.0
        if duration <= 0:
            continue
        timeline.append(
            {
                "speaker": str(item.get("speaker") or "SPEAKER"),
                "start": cursor,
                "end": cursor + duration,
                "text": str(item.get("text") or "")[:180],
            }
        )
        cursor += duration + gap_seconds
    return timeline


def _envelope(audio_path: str, fps: int, frames: int) -> np.ndarray:
    """Per-frame loudness (0..1) of the final mix."""
    result = audio_utils.read_audio(audio_path)
    if result is None:
        return np.zeros(frames, dtype="float32")
    samples, rate = result
    window = max(int(rate / fps), 1)
    levels = np.zeros(frames, dtype="float32")
    for i in range(frames):
        chunk = samples[i * window : (i + 1) * window]
        if chunk.size:
            levels[i] = float(np.sqrt(np.mean(np.square(chunk))))
    peak = float(levels.max()) or 1.0
    return np.clip(levels / peak, 0.0, 1.0)


def _background(size: Tuple[int, int]) -> Image.Image:
    width, height = size
    base = Image.new("RGB", (1, height))
    draw = ImageDraw.Draw(base)
    for y in range(height):
        t = y / max(height - 1, 1)
        draw.point(
            (0, y),
            fill=tuple(int(BG_TOP[c] + (BG_BOTTOM[c] - BG_TOP[c]) * t) for c in range(3)),
        )
    return base.resize((width, height))


def _initials(name: str) -> str:
    parts = [p for p in name.replace("_", " ").split() if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[1][0]).upper()


def _blend(a: Tuple[int, int, int], b: Tuple[int, int, int], t: float) -> Tuple[int, int, int]:
    t = max(0.0, min(1.0, t))
    return tuple(int(a[c] + (b[c] - a[c]) * t) for c in range(3))


def _draw_frame(
    background: Image.Image,
    speakers: List[str],
    colors: Dict[str, Tuple[int, int, int]],
    active: Optional[str],
    level: float,
    phase: float,
    caption: str,
    progress: float,
    title: str,
    fonts: Dict[str, ImageFont.ImageFont],
) -> Image.Image:
    frame = background.copy()
    draw = ImageDraw.Draw(frame)
    width, height = frame.size

    draw.text((56, 44), title, font=fonts["title"], fill=TEXT)
    draw.text((56, 84), "Video podcast", font=fonts["small"], fill=MUTED)

    count = max(len(speakers), 1)
    gap = 40
    stage_left, stage_right = 56, width - 56
    stage_top = 150
    card_w = int((stage_right - stage_left - gap * (count - 1)) / count)
    card_h = 340

    for index, speaker in enumerate(speakers):
        x0 = stage_left + index * (card_w + gap)
        y0 = stage_top
        x1, y1 = x0 + card_w, y0 + card_h
        is_active = speaker == active
        accent = colors[speaker]
        card = _blend(CARD_IDLE, CARD_ACTIVE, 1.0 if is_active else 0.0)
        draw.rounded_rectangle([x0, y0, x1, y1], radius=26, fill=card)
        if is_active:
            draw.rounded_rectangle([x0, y0, x1, y1], radius=26, outline=accent, width=3)

        # Avatar with a breathing ring driven by the audio level.
        cx = (x0 + x1) // 2
        cy = y0 + 132
        radius = 66
        if is_active:
            pulse = radius + 12 + level * 26 + math.sin(phase * 5.2) * 4
            draw.ellipse(
                [cx - pulse, cy - pulse, cx + pulse, cy + pulse],
                outline=_blend(card, accent, 0.55),
                width=4,
            )
        draw.ellipse(
            [cx - radius, cy - radius, cx + radius, cy + radius],
            fill=_blend(card, accent, 0.85 if is_active else 0.35),
        )
        initials = _initials(speaker)
        bbox = draw.textbbox((0, 0), initials, font=fonts["avatar"])
        draw.text(
            (cx - (bbox[2] - bbox[0]) / 2, cy - (bbox[3] - bbox[1]) / 2 - 6),
            initials,
            font=fonts["avatar"],
            fill=(16, 18, 24) if is_active else TEXT,
        )

        name = speaker.title()
        bbox = draw.textbbox((0, 0), name, font=fonts["name"])
        draw.text(
            (cx - (bbox[2] - bbox[0]) / 2, y0 + 216),
            name,
            font=fonts["name"],
            fill=TEXT if is_active else MUTED,
        )

        # Level meter — animated only for the speaker who currently has the mic.
        bars = 13
        bar_w = 8
        span = bars * bar_w + (bars - 1) * 7
        bx = cx - span // 2
        base_y = y0 + 300
        for b in range(bars):
            wobble = math.sin(phase * 6.5 + b * 0.8) * 0.5 + 0.5
            amount = (0.18 + level * wobble) if is_active else 0.08
            bar_h = int(6 + amount * 46)
            draw.rounded_rectangle(
                [bx + b * (bar_w + 7), base_y - bar_h, bx + b * (bar_w + 7) + bar_w, base_y],
                radius=4,
                fill=accent if is_active else (58, 66, 82),
            )

    if caption:
        cap_y = stage_top + card_h + 42
        draw.rounded_rectangle(
            [stage_left, cap_y, stage_right, cap_y + 96], radius=20, fill=(20, 24, 33)
        )
        wrapped = _wrap(caption, fonts["caption"], draw, stage_right - stage_left - 56)
        for line_index, line in enumerate(wrapped[:2]):
            draw.text(
                (stage_left + 28, cap_y + 22 + line_index * 34),
                line,
                font=fonts["caption"],
                fill=TEXT,
            )

    bar_y = height - 42
    draw.rounded_rectangle([56, bar_y, width - 56, bar_y + 8], radius=4, fill=(40, 46, 60))
    filled = 56 + int((width - 112) * max(0.0, min(1.0, progress)))
    if filled > 58:
        draw.rounded_rectangle([56, bar_y, filled, bar_y + 8], radius=4, fill=ACCENT_CYCLE[0])
    return frame


def _wrap(text: str, font, draw: ImageDraw.ImageDraw, max_width: int) -> List[str]:
    words = text.split()
    lines: List[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if draw.textlength(candidate, font=font) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def render_episode_video(
    audio_path: str,
    timeline: Sequence[Dict],
    output_path: str,
    title: str = "Podcast episode",
    fps: int = 10,
    size: Tuple[int, int] = (1280, 720),
    show_captions: bool = True,
) -> Optional[str]:
    """Render the talking-heads MP4. Returns the output path, or None on failure."""
    if not audio_path or not os.path.exists(audio_path) or not ffmpeg_available():
        return None

    duration = audio_utils.duration_seconds(audio_path) or 0.0
    if duration <= 0:
        return None

    speakers: List[str] = []
    for span in timeline:
        speaker = str(span.get("speaker") or "SPEAKER")
        if speaker not in speakers:
            speakers.append(speaker)
    if not speakers:
        speakers = ["SPEAKER"]
    speakers = speakers[:4]
    colors = {name: ACCENT_CYCLE[i % len(ACCENT_CYCLE)] for i, name in enumerate(speakers)}

    frames = int(duration * fps)
    if frames <= 0:
        return None
    levels = _envelope(audio_path, fps, frames)
    background = _background(size)
    fonts = {
        "title": _font(30),
        "small": _font(18),
        "name": _font(26),
        "avatar": _font(48),
        "caption": _font(22),
    }

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    workdir = tempfile.mkdtemp(prefix="episode_video_")
    try:
        span_index = 0
        spans = list(timeline)
        for i in range(frames):
            t = i / fps
            while span_index < len(spans) - 1 and t >= float(spans[span_index]["end"]):
                span_index += 1
            span = spans[span_index] if spans else None
            active = None
            caption = ""
            if span and float(span["start"]) <= t < float(span["end"]):
                active = str(span.get("speaker"))
                if active not in colors:
                    active = speakers[0]
                caption = str(span.get("text") or "") if show_captions else ""
            frame = _draw_frame(
                background,
                speakers,
                colors,
                active,
                float(levels[i]) if active else 0.0,
                t,
                caption,
                t / duration,
                title,
                fonts,
            )
            frame.save(os.path.join(workdir, f"f{i:06d}.png"))

        command = [
            "ffmpeg",
            "-y",
            "-framerate",
            str(fps),
            "-i",
            os.path.join(workdir, "f%06d.png"),
            "-i",
            audio_path,
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-pix_fmt",
            "yuv420p",
            "-r",
            "24",
            "-c:a",
            "aac",
            "-b:a",
            "160k",
            "-shortest",
            output_path,
        ]
        result = subprocess.run(command, capture_output=True, text=True, timeout=900)
        if result.returncode != 0 or not os.path.exists(output_path):
            return None
        return output_path
    except Exception:  # noqa: BLE001
        return None
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
