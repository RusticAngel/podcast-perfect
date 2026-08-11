"""Identify speakers and their characteristics from a transcript."""

from typing import Dict, List


class SpeakerIdentifier:
    """Derive speaker profiles from parsed dialogue segments."""

    HOST_HINTS = ("host", "narrator", "anchor", "moderator")
    GUEST_HINTS = ("guest", "expert", "caller", "interviewee")

    def identify(self, dialogue_segments: List[Dict]) -> Dict[str, Dict]:
        """Return a mapping of speaker -> profile."""
        profiles: Dict[str, Dict] = {}

        for segment in dialogue_segments:
            speaker = (segment.get("speaker") or "NARRATOR").strip()
            text = segment.get("text", "")
            profile = profiles.setdefault(
                speaker,
                {"name": speaker, "line_count": 0, "word_count": 0, "role": "unknown"},
            )
            profile["line_count"] += 1
            profile["word_count"] += len(text.split())

        total_words = sum(p["word_count"] for p in profiles.values()) or 1
        ordered = sorted(profiles.values(), key=lambda p: p["word_count"], reverse=True)

        for index, profile in enumerate(ordered):
            name_lower = profile["name"].lower()
            if any(h in name_lower for h in self.HOST_HINTS):
                profile["role"] = "host"
            elif any(h in name_lower for h in self.GUEST_HINTS):
                profile["role"] = "guest"
            else:
                profile["role"] = "host" if index == 0 else "guest"

            profile["share_of_dialogue"] = round(
                profile["word_count"] / total_words, 3
            )
            profile["speaking_style"] = self._style(profile)

        return profiles

    def _style(self, profile: Dict) -> str:
        avg = profile["word_count"] / max(profile["line_count"], 1)
        if avg > 60:
            return "long-form, expository"
        if avg > 25:
            return "conversational"
        return "punchy, reactive"

    def assign_voices(
        self,
        profiles: Dict[str, Dict],
        voices: List[str],
    ) -> Dict[str, str]:
        """Deterministically assign a TTS voice to each speaker."""
        if not voices:
            return {}
        assignment: Dict[str, str] = {}
        for index, speaker in enumerate(sorted(profiles.keys())):
            assignment[speaker] = voices[index % len(voices)]
        return assignment
