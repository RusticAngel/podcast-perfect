"""Extract structured data from podcast script PDFs."""

import re
from typing import Dict, List

import PyPDF2


class PDFScriptParser:
    """Extract structured data from podcast script PDFs."""

    def __init__(self):
        self.speaker_pattern = r'^([A-Z][A-Z\s]+):'
        self.scene_pattern = r'(INT\.|EXT\.|SCENE|CHAPTER)'
        self.mood_keywords = [
            'happy', 'sad', 'excited', 'angry', 'calm', 'nervous', 'funny', 'serious'
        ]

    def parse(self, pdf_path: str) -> Dict:
        """Extract text and structured data from PDF."""
        text = self._extract_text(pdf_path)

        return {
            "full_text": text,
            "speakers": self._extract_speakers(text),
            "dialogue_segments": self._extract_dialogue_segments(text),
            "topics": self._extract_topics(text),
            "mood": self._detect_mood(text),
            "scene_breaks": self._detect_scene_breaks(text),
            "estimated_duration": self._calculate_duration(text),
        }

    def parse_text(self, text: str) -> Dict:
        """Parse a raw transcript string (no PDF)."""
        return {
            "full_text": text,
            "speakers": self._extract_speakers(text),
            "dialogue_segments": self._extract_dialogue_segments(text),
            "topics": self._extract_topics(text),
            "mood": self._detect_mood(text),
            "scene_breaks": self._detect_scene_breaks(text),
            "estimated_duration": self._calculate_duration(text),
        }

    def _extract_text(self, pdf_path: str) -> str:
        """Extract raw text from PDF."""
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += (page.extract_text() or "") + "\n"
        return text

    def _extract_speakers(self, text: str) -> List[str]:
        """Extract speaker names from script."""
        matches = re.findall(self.speaker_pattern, text, re.MULTILINE)
        return sorted({m.strip() for m in matches})

    def _extract_dialogue_segments(self, text: str) -> List[Dict]:
        """Extract dialogue with speaker attribution."""
        segments: List[Dict] = []
        lines = text.split('\n')
        current_speaker = None
        current_dialogue: List[str] = []

        for line in lines:
            speaker_match = re.match(self.speaker_pattern, line)
            if speaker_match:
                if current_speaker and current_dialogue:
                    segments.append({
                        "speaker": current_speaker,
                        "text": ' '.join(current_dialogue).strip(),
                    })
                current_speaker = speaker_match.group(1).strip()
                current_dialogue = [re.sub(self.speaker_pattern, '', line).strip()]
            elif current_speaker:
                current_dialogue.append(line.strip())

        if current_speaker and current_dialogue:
            segments.append({
                "speaker": current_speaker,
                "text": ' '.join(current_dialogue).strip(),
            })

        return segments

    def _extract_topics(self, text: str) -> List[str]:
        """Extract key topics using keyword frequency analysis."""
        stopwords = {
            'this', 'that', 'with', 'have', 'from', 'they', 'been', 'were',
            'what', 'when', 'your', 'about', 'there', 'their', 'would',
            'which', 'these', 'them', 'just', 'like', 'know', 'yeah',
        }
        words = re.findall(r'\b[A-Za-z]{4,}\b', text.lower())
        word_freq: Dict[str, int] = {}
        for word in words:
            if word in stopwords:
                continue
            word_freq[word] = word_freq.get(word, 0) + 1
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, _ in sorted_words[:10]]

    def _detect_mood(self, text: str) -> str:
        """Detect overall mood from script."""
        lower_text = text.lower()
        mood_counts = {mood: lower_text.count(mood) for mood in self.mood_keywords}
        best = max(mood_counts, key=lambda m: mood_counts[m])
        return best if mood_counts[best] > 0 else "neutral"

    def _detect_scene_breaks(self, text: str) -> int:
        """Count scene breaks."""
        return len(re.findall(self.scene_pattern, text))

    def _calculate_duration(self, text: str) -> int:
        """Estimate audio duration in minutes (~150 wpm)."""
        word_count = len(re.findall(r'\b\w+\b', text))
        return word_count // 150
