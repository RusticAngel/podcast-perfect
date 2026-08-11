import pytest

from src.phase2_document_processing.pdf_parser import PDFScriptParser
from src.phase2_document_processing.script_analyzer import ScriptAnalyzer
from src.phase2_document_processing.speaker_identifier import SpeakerIdentifier

SCRIPT = """HOST: Welcome back to the show. Today we are talking about serious
climate technology and why it matters.
GUEST: Thanks for having me. I am excited to dig into carbon capture.
HOST: Let's start with the basics.
"""


@pytest.fixture
def parser():
    return PDFScriptParser()


def test_extract_speakers(parser):
    speakers = parser._extract_speakers(SCRIPT)
    assert "HOST" in speakers
    assert "GUEST" in speakers


def test_dialogue_segments(parser):
    segments = parser._extract_dialogue_segments(SCRIPT)
    assert len(segments) == 3
    assert segments[0]["speaker"] == "HOST"
    assert "Welcome back" in segments[0]["text"]


def test_topics_exclude_stopwords(parser):
    topics = parser._extract_topics(SCRIPT)
    assert "this" not in topics
    assert len(topics) <= 10


def test_mood_detection(parser):
    assert parser._detect_mood(SCRIPT) in {"serious", "excited"}
    assert parser._detect_mood("plain text") == "neutral"


def test_duration_estimate(parser):
    assert parser._calculate_duration("word " * 300) == 2


def test_parse_text_shape(parser):
    data = parser.parse_text(SCRIPT)
    assert set(
        ["full_text", "speakers", "dialogue_segments", "topics", "mood"]
    ).issubset(data)


def test_speaker_profiles(parser):
    segments = parser._extract_dialogue_segments(SCRIPT)
    profiles = SpeakerIdentifier().identify(segments)
    assert profiles["HOST"]["role"] == "host"
    assert profiles["GUEST"]["role"] == "guest"
    assert 0 < profiles["HOST"]["share_of_dialogue"] <= 1


def test_script_analyzer_structure(parser):
    data = parser.parse_text(SCRIPT)
    analysis = ScriptAnalyzer().analyze(data)
    assert analysis["segment_count"] == 3
    assert analysis["music_direction"]
    assert analysis["production_notes"]
