"""Extract topics, structure, and mood from a parsed script."""

from typing import Dict, List


class ScriptAnalyzer:
    """Heuristic, offline structural analysis of a podcast script."""

    MOOD_MUSIC = {
        "happy": "upbeat acoustic",
        "excited": "energetic electronic",
        "sad": "melancholic piano",
        "angry": "tense percussion",
        "calm": "ambient pads",
        "nervous": "sparse suspense",
        "funny": "playful ukulele",
        "serious": "documentary strings",
        "neutral": "soft lo-fi",
    }

    def analyze(self, script_data: Dict) -> Dict:
        segments = script_data.get("dialogue_segments", [])
        mood = script_data.get("mood", "neutral")

        return {
            "structure": self._structure(segments),
            "topics": script_data.get("topics", []),
            "mood": mood,
            "music_direction": self.MOOD_MUSIC.get(mood, "soft lo-fi"),
            "segment_count": len(segments),
            "production_notes": self._production_notes(script_data),
        }

    def _structure(self, segments: List[Dict]) -> Dict:
        total = len(segments)
        if total == 0:
            return {"intro": [], "body": [], "outro": []}
        intro_end = max(1, total // 10)
        outro_start = max(intro_end, total - max(1, total // 10))
        return {
            "intro": segments[:intro_end],
            "body": segments[intro_end:outro_start],
            "outro": segments[outro_start:],
        }

    def _production_notes(self, script_data: Dict) -> List[str]:
        notes = ["Fade in theme music over the first 8 seconds of the intro."]
        duration = script_data.get("estimated_duration", 0)
        if duration > 45:
            notes.append("Insert a mid-roll break around the halfway mark.")
        if script_data.get("scene_breaks", 0) > 0:
            notes.append("Use a short音 sting between scene breaks.".replace("音", " "))
        notes.append("Duck background music by 12 dB under dialogue.")
        return notes
