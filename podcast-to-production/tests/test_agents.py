"""Agent tests that stub out Google Cloud so they run offline."""

import types

import pytest

from src.phase2_document_processing.pdf_parser import PDFScriptParser

SCRIPT = """HOST: Welcome to the pilot episode about generative audio.
GUEST: Happy to be here, this is exciting work.
"""


@pytest.fixture
def script_data():
    parser = PDFScriptParser()
    data = parser.parse_text(SCRIPT)
    data["genre"] = "technology"
    return data


@pytest.fixture
def director(monkeypatch):
    from src.phase4_adk_agents import director_agent

    monkeypatch.setattr(
        director_agent.DirectorAgent, "__init__", lambda self, model_name="m": None
    )
    agent = director_agent.DirectorAgent()
    agent.model_name = "gemini-2.0-flash-exp"
    return agent


def test_director_falls_back_to_local_analysis(director, script_data, monkeypatch):
    monkeypatch.setattr(
        director,
        "create_agent",
        lambda: (_ for _ in ()).throw(RuntimeError("no cloud creds")),
    )
    result = director.run(script_data)
    assert result["fallback"] is True
    assert result["segments"] == 2
    assert "HOST" in result["speakers"]


def test_director_uses_agent_when_available(director, script_data, monkeypatch):
    fake = types.SimpleNamespace(run=lambda payload: {"tone": "curious"})
    monkeypatch.setattr(director, "create_agent", lambda: fake)
    assert director.run(script_data)["tone"] == "curious"


def test_producer_assigns_alternating_voices(monkeypatch):
    from src.phase4_adk_agents import audio_producer_agent

    monkeypatch.setattr(
        audio_producer_agent.AudioProducerAgent,
        "__init__",
        lambda self, model_name="m": None,
    )
    agent = audio_producer_agent.AudioProducerAgent()
    voices = {agent._assign_voice(s, ["GUEST", "HOST"]) for s in ("HOST", "GUEST")}
    assert len(voices) == 2


def test_producer_produce_audio_pipeline(monkeypatch, script_data):
    from src.phase4_adk_agents import audio_producer_agent

    monkeypatch.setattr(
        audio_producer_agent.AudioProducerAgent,
        "__init__",
        lambda self, model_name="m": None,
    )
    agent = audio_producer_agent.AudioProducerAgent()
    agent.tts_tool = types.SimpleNamespace(
        generate_speech=lambda text, voice: f"/tmp/{voice}.wav"
    )
    agent.music_tool = types.SimpleNamespace(
        generate_music=lambda mood, duration_seconds=30: "/tmp/music.wav"
    )
    agent.sentiment_tool = types.SimpleNamespace(
        analyze_sentiment=lambda script_text: {"overall_tone": "positive"}
    )

    result = agent._produce_audio({
        "dialogue_segments": script_data["dialogue_segments"],
        "speakers": script_data["speakers"],
        "tone": "excited",
    })
    assert result["total_segments"] == 2
    assert result["music_path"] == "/tmp/music.wav"
    assert result["sentiment_analysis"]["overall_tone"] == "positive"


def test_orchestrator_recommendations(monkeypatch, script_data):
    from src.phase4_adk_agents import orchestrator as orch

    monkeypatch.setattr(orch.PodcastOrchestrator, "__init__", lambda self: None)
    coordinator = orch.PodcastOrchestrator()
    script_data["estimated_duration"] = 90
    recs = coordinator._generate_recommendations(
        script_data,
        {},
        {"market_research": [{"title": "Show X"}]},
    )
    assert any("Show X" in r for r in recs)
    assert any("2 parts" in r for r in recs)
