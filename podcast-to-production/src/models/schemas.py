"""Pydantic models for the API."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ScriptRequest(BaseModel):
    genre: Optional[str] = "general"


class DialogueSegment(BaseModel):
    speaker: str
    text: str


class ScriptAnalysis(BaseModel):
    full_text: str = ""
    speakers: List[str] = Field(default_factory=list)
    dialogue_segments: List[DialogueSegment] = Field(default_factory=list)
    topics: List[str] = Field(default_factory=list)
    mood: str = "neutral"
    scene_breaks: int = 0
    estimated_duration: int = 0


class AudioAsset(BaseModel):
    speaker: str
    text: str
    audio_path: Optional[str] = None
    voice: Optional[str] = None


class AudioProduction(BaseModel):
    audio_files: List[AudioAsset] = Field(default_factory=list)
    music_path: Optional[str] = None
    sentiment_analysis: Dict[str, Any] = Field(default_factory=dict)
    total_segments: int = 0


class ProcessResponse(BaseModel):
    status: str
    script_analysis: Dict[str, Any]
    director_notes: Dict[str, Any]
    market_research: Dict[str, Any]
    audio_production: Dict[str, Any]
    recommendations: List[str] = Field(default_factory=list)
    download_url: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    services: List[str]
