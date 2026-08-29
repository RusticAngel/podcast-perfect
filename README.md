# Podcast Perfect

# ROLE: Senior AI Architect & Hackathon Winner

You are building a submission for the **Google Cloud Agentic Cinema Hackathon** (Deadline: Sept 7, 2026, $75k total prizes).

## ⚠️ CRITICAL RULES (Must Follow)
1. The FINAL PROJECT must use ONLY Google Cloud AI tools at runtime:
   - **Gemini Enterprise** via `google-genai` SDK for ALL agent reasoning
   - **Google Cloud Agent Engine** via `google-cloud-aiplatform[agent_engines,adk]>=1.101.0`
   - **Gemini TTS** for speech generation
   - **Lyria 3** for music generation (via Google Cloud)
   - **Sentiment Analysis** via Gemini multimodal
2. YOU (DeepSeek) are my coding assistant writing the code. DeepSeek is NOT used in the final deployed project.
3. Partner Integration: **Parallel Search API** at runtime (free for OpenCode agents)
4. The project must solve a **media/entertainment workflow problem**.

## MY CHOSEN PROJECT: "Podcast-to-Production Agent"

### Project Description
A multi-agent system that takes a podcast script or interview transcript (PDF) and automatically generates a complete, production-ready podcast episode with:
- Multi-speaker audio using different AI voices (Gemini TTS)
- Background music matching the script's mood/tone (Lyria 3)
- Sentiment analysis comparing script tone vs. audio delivery
- Research on similar successful podcasts (Parallel Search)
- Production readiness report

### Media Workflow (Entertainment Focus)
**Target Audience:** Podcasters, audiobook producers, content creators, indie filmmakers, and studio production teams.

**Problem Solved:** Podcast production currently takes 5-10 hours per episode (scripting, recording, editing, music, mastering). This agent reduces it to 5 minutes.

## COMPLETE FILE STRUCTURE

Generate the following exact folder structure with ALL files:

```

/podcast-to-production/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── README.md
├── LICENSE                          # Apache 2.0
├── src/
│   ├── init.py
│   ├── main.py                      # FastAPI application
│   ├── config.py                    # Environment variables
│   │
│   ├── phase2_document_processing/
│   │   ├── init.py
│   │   ├── pdf_parser.py            # Extract text from PDF scripts
│   │   ├── speaker_identifier.py    # Identify speakers from transcript
│   │   └── script_analyzer.py       # Extract topics, structure, mood
│   │
│   ├── phase3_partner_integration/
│   │   ├── init.py
│   │   └── parallel_search.py       # Parallel Search API wrapper
│   │
│   ├── phase4_adk_agents/
│   │   ├── init.py
│   │   ├── base_agent.py            # Abstract ADK agent class
│   │   ├── director_agent.py        # Script analysis (Gemini)
│   │   ├── researcher_agent.py      # Web research (Gemini + Parallel)
│   │   ├── audio_producer_agent.py  # TTS + Music generation (Gemini + Lyria)
│   │   └── orchestrator.py          # Multi-agent workflow coordinator
│   │
│   ├── phase5_deployment/
│   │   ├── init.py
│   │   ├── cloud_run.py             # Cloud Run configuration
│   │   └── secret_manager.py        # Secure API key management
│   │
│   ├── tools/
│   │   ├── init.py
│   │   ├── gemini_tts.py            # Gemini TTS wrapper (multi-speaker)
│   │   ├── lyria_music.py           # Lyria 3 music generation
│   │   ├── sentiment_analyzer.py    # Multimodal sentiment analysis
│   │   └── audio_utils.py           # Audio processing utilities
│   │
│   ├── models/
│   │   ├── init.py
│   │   └── schemas.py               # Pydantic models for API
│   │
│   └── utils/
│       ├── init.py
│       └── file_handlers.py         # File upload/download utilities
│
├── tests/
│   ├── init.py
│   ├── test_pdf_parser.py
│   ├── test_parallel_api.py
│   └── test_agents.py
│
├── static/
│   └── demo_script.pdf              # Sample podcast script for demo
│
└── notebooks/
└── agent_test.ipynb             # ADK testing notebook

```

---

## IMPLEMENTATION DETAILS

### 1. requirements.txt
```

google-cloud-aiplatform[agent_engines,adk]>=1.101.0
google-genai>=0.1.0
PyPDF2>=3.0.0
fastapi>=0.115.0
uvicorn>=0.30.0
python-multipart>=0.0.9
pydantic>=2.5.0
python-dotenv>=1.0.0
parallel-web>=0.1.0
librosa>=0.10.0
soundfile>=0.12.0
numpy>=1.26.0
pandas>=2.1.0
requests>=2.31.0

```

### 2. .env.example
```

Google Cloud

GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=./credentials.json

Gemini API

GEMINI_API_KEY=your-gemini-key
GEMINI_MODEL=gemini-2.0-flash-exp

Parallel Search (free for OpenCode agents)

PARALLEL_API_KEY=your-parallel-key  # Optional

Cloud Run

CLOUD_RUN_URL=your-cloud-run-url

Lyria 3 (music generation)

LYRIA_API_KEY=your-lyria-key  # Optional, may use free tier

TTS Configuration

DEFAULT_TTS_VOICE=en-US-Neural2-F
SECONDARY_TTS_VOICE=en-US-Neural2-M

```

### 3. config.py (src/config.py)
```python
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Google Cloud
    PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
    CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    # Gemini
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp")
    
    # Parallel
    PARALLEL_API_KEY = os.getenv("PARALLEL_API_KEY")
    
    # Lyria
    LYRIA_API_KEY = os.getenv("LYRIA_API_KEY")
    
    # TTS
    DEFAULT_VOICE = os.getenv("DEFAULT_TTS_VOICE", "en-US-Neural2-F")
    SECONDARY_VOICE = os.getenv("SECONDARY_TTS_VOICE", "en-US-Neural2-M")
    
    # Directories
    UPLOAD_DIR = "./uploads"
    OUTPUT_DIR = "./outputs"
    STATIC_DIR = "./static"
```

4. Phase 2: Document Processing (pdf_parser.py)

```python
# src/phase2_document_processing/pdf_parser.py
import PyPDF2
import re
from typing import Dict, List, Tuple
import os

class PDFScriptParser:
    """Extract structured data from podcast script PDFs."""
    
    def __init__(self):
        self.speaker_pattern = r'^([A-Z][A-Z\s]+):'
        self.scene_pattern = r'(INT\.|EXT\.|SCENE|CHAPTER)'
        self.mood_keywords = ['happy', 'sad', 'excited', 'angry', 'calm', 'nervous', 'funny', 'serious']
    
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
            "estimated_duration": self._calculate_duration(text)
        }
    
    def _extract_text(self, pdf_path: str) -> str:
        """Extract raw text from PDF."""
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
        return text
    
    def _extract_speakers(self, text: str) -> List[str]:
        """Extract speaker names from script."""
        matches = re.findall(self.speaker_pattern, text, re.MULTILINE)
        return list(set(matches))
    
    def _extract_dialogue_segments(self, text: str) -> List[Dict]:
        """Extract dialogue with speaker attribution."""
        segments = []
        lines = text.split('\n')
        current_speaker = None
        current_dialogue = []
        
        for line in lines:
            speaker_match = re.match(self.speaker_pattern, line)
            if speaker_match:
                if current_speaker and current_dialogue:
                    segments.append({
                        "speaker": current_speaker,
                        "text": ' '.join(current_dialogue).strip()
                    })
                current_speaker = speaker_match.group(1)
                current_dialogue = [re.sub(self.speaker_pattern, '', line).strip()]
            elif current_speaker:
                current_dialogue.append(line.strip())
        
        # Add last segment
        if current_speaker and current_dialogue:
            segments.append({
                "speaker": current_speaker,
                "text": ' '.join(current_dialogue).strip()
            })
        
        return segments
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract key topics using keyword analysis."""
        # Simple keyword extraction
        words = re.findall(r'\b[A-Za-z]{4,}\b', text)
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, count in sorted_words[:10]]
    
    def _detect_mood(self, text: str) -> str:
        """Detect overall mood from script."""
        mood_counts = {mood: 0 for mood in self.mood_keywords}
        lower_text = text.lower()
        for mood in self.mood_keywords:
            mood_counts[mood] = lower_text.count(mood)
        return max(mood_counts, key=mood_counts.get)
    
    def _detect_scene_breaks(self, text: str) -> int:
        """Count scene breaks."""
        matches = re.findall(self.scene_pattern, text)
        return len(matches)
    
    def _calculate_duration(self, text: str) -> int:
        """Estimate audio duration in minutes."""
        word_count = len(re.findall(r'\b\w+\b', text))
        return word_count // 150  # ~150 words per minute
```

5. Phase 3: Partner Integration (parallel_search.py)

```python
# src/phase3_partner_integration/parallel_search.py
from parallel_web import ParallelSearch
from typing import List, Dict, Optional
import os

class ParallelResearchTool:
    """Ground agents in real-time web data using Parallel Search."""
    
    def __init__(self, api_key: Optional[str] = None):
        # Parallel is free for OpenCode agents
        self.api_key = api_key or os.getenv("PARALLEL_API_KEY")
        self.client = ParallelSearch(api_key=self.api_key) if self.api_key else None
    
    def search_podcast_data(self, topic: str, genre: str = None) -> List[Dict]:
        """Search for podcast industry data."""
        query = f"best {genre if genre else ''} podcasts about {topic} audience engagement trends"
        return self._search(query)
    
    def search_competitor_analysis(self, podcast_title: str) -> List[Dict]:
        """Research similar podcasts."""
        query = f"{podcast_title} podcast review ratings audience size"
        return self._search(query)
    
    def _search(self, query: str, max_results: int = 10) -> List[Dict]:
        """Execute search and return structured results."""
        if not self.client:
            return [{"error": "Parallel API key not configured"}]
        
        try:
            response = self.client.search(
                query=query,
                max_results=max_results
            )
            return [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "snippet": r.get("snippet", ""),
                    "published_date": r.get("published_date", "")
                }
                for r in response.get("results", [])
            ]
        except Exception as e:
            return [{"error": str(e)}]
```

6. Phase 4: ADK Multi-Agent System

Base Agent (base_agent.py)

```python
# src/phase4_adk_agents/base_agent.py
from abc import ABC, abstractmethod
from google.cloud import aiplatform
from vertexai.preview import reasoning_engines
from typing import Any, Dict
import os

class BaseAgent(ABC):
    """Abstract base class for all ADK agents."""
    
    def __init__(self, model_name: str = "gemini-2.0-flash-exp"):
        self.model_name = model_name
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = "us-central1"
        
        # Initialize Vertex AI
        aiplatform.init(
            project=self.project_id,
            location=self.location
        )
    
    @abstractmethod
    def create_agent(self) -> reasoning_engines.ReasoningEngine:
        """Create and return the ADK agent instance."""
        pass
    
    @abstractmethod
    def run(self, input_data: Any) -> Any:
        """Run the agent with given input."""
        pass
```

Director Agent (director_agent.py)

```python
# src/phase4_adk_agents/director_agent.py
from vertexai.preview import reasoning_engines
from typing import Dict, Any
from .base_agent import BaseAgent

class DirectorAgent(BaseAgent):
    """Analyzes script structure, tone, and production requirements."""
    
    def create_agent(self) -> reasoning_engines.ReasoningEngine:
        return reasoning_engines.ReasoningEngine.from_config({
            "model": self.model_name,
            "system_instruction": """
            You are a Podcast Director AI. Your role is to analyze podcast scripts and prepare them for production.
            
            TASKS:
            1. Analyze script structure (intro, segments, outro)
            2. Identify speaker roles and their speaking patterns
            3. Determine overall tone and mood
            4. Suggest pacing and emphasis for different sections
            5. Identify production cues (music, sound effects, pauses)
            
            OUTPUT FORMAT:
            Return a JSON with:
            - structure: dict with sections
            - speakers: list with speaking style notes
            - tone: string describing overall mood
            - pacing: recommendations for each section
            - production_notes: list of cues
            """,
            "tools": [self._analyze_structure]
        })
    
    def run(self, script_data: Dict) -> Dict:
        """Run director analysis on script data."""
        agent = self.create_agent()
        result = agent.run({
            "script_text": script_data.get("full_text", ""),
            "speakers": script_data.get("speakers", []),
            "dialogue_segments": script_data.get("dialogue_segments", []),
            "mood": script_data.get("mood", "neutral"),
            "estimated_duration": script_data.get("estimated_duration", 30)
        })
        return result
    
    def _analyze_structure(self, script_data: Dict) -> Dict:
        """Tool function for analyzing script structure."""
        # This is a simplified version - in production, this would be more sophisticated
        segments = script_data.get("dialogue_segments", [])
        total_words = len(script_data.get("full_text", "").split())
        
        return {
            "segments": len(segments),
            "speakers": list(set([s.get("speaker") for s in segments if s.get("speaker")])),
            "total_words": total_words,
            "estimated_podcast_duration_minutes": total_words / 150
        }
```

Researcher Agent (researcher_agent.py)

```python
# src/phase4_adk_agents/researcher_agent.py
from vertexai.preview import reasoning_engines
from typing import Dict, Any
from .base_agent import BaseAgent
from src.phase3_partner_integration.parallel_search import ParallelResearchTool

class ResearcherAgent(BaseAgent):
    """Researches podcast market using Parallel Search API."""
    
    def __init__(self, model_name: str = "gemini-2.0-flash-exp"):
        super().__init__(model_name)
        self.parallel_tool = ParallelResearchTool()
    
    def create_agent(self) -> reasoning_engines.ReasoningEngine:
        return reasoning_engines.ReasoningEngine.from_config({
            "model": self.model_name,
            "system_instruction": """
            You are a Podcast Research AI. Your role is to provide market intelligence for podcast production.
            
            TASKS:
            1. Research successful podcasts in similar genres
            2. Identify audience preferences and trends
            3. Find comparable podcast formats and structures
            4. Gather data on episode lengths, release schedules, and engagement
            5. Provide recommendations based on market data
            
            OUTPUT FORMAT:
            Return a JSON with:
            - market_data: dict with findings
            - comparable_podcasts: list with details
            - audience_insights: dict with demographics and preferences
            - recommendations: list of actionable suggestions
            """,
            "tools": [self._search_podcast_market]
        })
    
    def run(self, script_data: Dict, director_analysis: Dict) -> Dict:
        """Run research based on script content and director analysis."""
        agent = self.create_agent()
        result = agent.run({
            "topics": director_analysis.get("topics", []),
            "genre": script_data.get("genre", "general"),
            "mood": script_data.get("mood", "neutral"),
            "estimated_duration": script_data.get("estimated_duration", 30)
        })
        return result
    
    def _search_podcast_market(self, research_params: Dict) -> Dict:
        """Tool function for searching podcast market data."""
        topics = research_params.get("topics", [])
        genre = research_params.get("genre", "general")
        
        results = []
        for topic in topics[:3]:
            search_results = self.parallel_tool.search_podcast_data(topic, genre)
            results.extend(search_results)
        
        return {
            "market_research": results[:10],
            "similar_podcasts_count": len(results),
            "trending_topics": topics[:5]
        }
```

Audio Producer Agent (audio_producer_agent.py)

```python
# src/phase4_adk_agents/audio_producer_agent.py
from vertexai.preview import reasoning_engines
from typing import Dict, Any
from .base_agent import BaseAgent
from src.tools.gemini_tts import GeminiTTSTool
from src.tools.lyria_music import LyriaMusicTool
from src.tools.sentiment_analyzer import SentimentAnalyzerTool

class AudioProducerAgent(BaseAgent):
    """Generates audio assets using Gemini TTS and Lyria 3."""
    
    def __init__(self, model_name: str = "gemini-2.0-flash-exp"):
        super().__init__(model_name)
        self.tts_tool = GeminiTTSTool()
        self.music_tool = LyriaMusicTool()
        self.sentiment_tool = SentimentAnalyzerTool()
    
    def create_agent(self) -> reasoning_engines.ReasoningEngine:
        return reasoning_engines.ReasoningEngine.from_config({
            "model": self.model_name,
            "system_instruction": """
            You are an Audio Production AI. Your role is to generate high-quality audio assets for podcast production.
            
            TASKS:
            1. Convert script text to speech using Gemini TTS (multi-speaker)
            2. Generate appropriate background music using Lyria 3
            3. Perform sentiment analysis on audio vs. script
            4. Ensure audio quality and timing
            5. Output complete audio files
            
            OUTPUT FORMAT:
            Return a JSON with:
            - audio_files: dict with paths to generated audio
            - music_files: dict with paths to background music
            - sentiment_analysis: dict with tone comparisons
            - production_notes: dict with timing and quality metrics
            """,
            "tools": [self._produce_audio]
        })
    
    def run(self, script_data: Dict, director_analysis: Dict) -> Dict:
        """Generate audio assets from script and analysis."""
        agent = self.create_agent()
        result = agent.run({
            "dialogue_segments": script_data.get("dialogue_segments", []),
            "speakers": script_data.get("speakers", []),
            "tone": director_analysis.get("tone", "neutral"),
            "pacing": director_analysis.get("pacing", {}),
            "structure": director_analysis.get("structure", {})
        })
        return result
    
    def _produce_audio(self, production_params: Dict) -> Dict:
        """Tool function for audio production."""
        segments = production_params.get("dialogue_segments", [])
        speakers = production_params.get("speakers", [])
        tone = production_params.get("tone", "neutral")
        
        # Generate TTS for each speaker
        audio_files = []
        for segment in segments:
            speaker = segment.get("speaker", "Narrator")
            text = segment.get("text", "")
            
            # Assign voice based on speaker
            voice = self._assign_voice(speaker, speakers)
            audio_path = self.tts_tool.generate_speech(text, voice)
            audio_files.append({
                "speaker": speaker,
                "text": text,
                "audio_path": audio_path,
                "voice": voice
            })
        
        # Generate background music
        music_path = self.music_tool.generate_music(tone, duration_seconds=30)
        
        # Analyze sentiment
        sentiment = self.sentiment_tool.analyze_sentiment(
            script_text=" ".join([s.get("text", "") for s in segments])
        )
        
        return {
            "audio_files": audio_files,
            "music_path": music_path,
            "sentiment_analysis": sentiment,
            "total_segments": len(segments)
        }
    
    def _assign_voice(self, speaker: str, speakers: list) -> str:
        """Assign TTS voice based on speaker role."""
        if len(speakers) > 1:
            if speakers.index(speaker) % 2 == 0:
                return "en-US-Neural2-F"
            else:
                return "en-US-Neural2-M"
        return "en-US-Neural2-F"
```

Orchestrator (orchestrator.py)

```python
# src/phase4_adk_agents/orchestrator.py
from typing import Dict, Any
from .director_agent import DirectorAgent
from .researcher_agent import ResearcherAgent
from .audio_producer_agent import AudioProducerAgent
from src.phase2_document_processing.pdf_parser import PDFScriptParser
from src.phase3_partner_integration.parallel_search import ParallelResearchTool
import json
import os

class PodcastOrchestrator:
    """Orchestrates the complete multi-agent workflow."""
    
    def __init__(self):
        self.director = DirectorAgent()
        self.researcher = ResearcherAgent()
        self.producer = AudioProducerAgent()
        self.parser = PDFScriptParser()
        self.parallel_tool = ParallelResearchTool()
    
    def process_script(self, pdf_path: str, genre: str = "general") -> Dict:
        """
        Complete multi-agent pipeline:
        1. Parse PDF -> structured data
        2. Director analyzes structure and tone
        3. Researcher finds market intelligence
        4. Producer generates audio assets
        """
        print("📄 Step 1: Parsing PDF script...")
        script_data = self.parser.parse(pdf_path)
        script_data["genre"] = genre
        
        print("🎬 Step 2: Director analyzing script...")
        director_analysis = self.director.run(script_data)
        
        print("🔍 Step 3: Researcher gathering market data...")
        research = self.researcher.run(script_data, director_analysis)
        
        print("🎵 Step 4: Producer generating audio...")
        audio_output = self.producer.run(script_data, director_analysis)
        
        print("✅ Orchestration complete!")
        
        return {
            "script_analysis": script_data,
            "director_notes": director_analysis,
            "market_research": research,
            "audio_production": audio_output,
            "recommendations": self._generate_recommendations(
                script_data, director_analysis, research
            ),
            "status": "success"
        }
    
    def _generate_recommendations(self, script_data: Dict, analysis: Dict, research: Dict) -> list:
        """Generate production recommendations."""
        recommendations = []
        
        # Based on script analysis
        if len(script_data.get("speakers", [])) > 3:
            recommendations.append("Consider assigning unique voices to each speaker for better listener engagement.")
        
        # Based on market research
        similar_podcasts = research.get("market_data", {}).get("comparable_podcasts", [])
        if similar_podcasts:
            recommendations.append(f"Format similar to {similar_podcasts[0].get('title', 'popular podcasts')} - consider adopting their pacing.")
        
        # Based on estimated duration
        duration = script_data.get("estimated_duration", 30)
        if duration > 60:
            recommendations.append("Consider breaking this episode into 2 parts for better listener retention.")
        
        return recommendations
```

7. Tools: Gemini TTS (gemini_tts.py)

```python
# src/tools/gemini_tts.py
import os
import base64
from google import genai
from typing import Optional
import soundfile as sf
import numpy as np

class GeminiTTSTool:
    """Generate speech using Gemini TTS."""
    
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=api_key)
    
    def generate_speech(self, text: str, voice: str = "en-US-Neural2-F") -> str:
        """Generate speech audio from text."""
        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=f"Convert this text to speech with voice {voice}: {text}",
                config={
                    "response_modalities": ["AUDIO"],
                    "voice_config": {
                        "voice_name": voice
                    }
                }
            )
            
            # Save audio
            output_path = f"./outputs/speech_{hash(text)}.wav"
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Write audio data
            with open(output_path, "wb") as f:
                f.write(response.candidates[0].content.parts[0].data)
            
            return output_path
            
        except Exception as e:
            print(f"TTS error: {e}")
            return None
```

8. Tools: Lyria Music Generator (lyria_music.py)

```python
# src/tools/lyria_music.py
import os
import requests
from typing import Optional

class LyriaMusicTool:
    """Generate background music using Lyria 3."""
    
    def __init__(self):
        self.api_key = os.getenv("LYRIA_API_KEY")
        self.base_url = "https://lyria.googleapis.com/v3/generate"
    
    def generate_music(self, mood: str = "calm", duration_seconds: int = 30) -> Optional[str]:
        """Generate background music matching the mood."""
        try:
            # Lyria 3 API call (simplified)
            response = requests.post(
                self.base_url,
                json={
                    "mood": mood,
                    "duration": duration_seconds,
                    "genre": "podcast_background",
                    "instrumentation": "piano, soft strings"
                },
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            
            if response.status_code == 200:
                output_path = f"./outputs/music_{hash(mood)}.wav"
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(response.content)
                return output_path
            
            return None
            
        except Exception as e:
            print(f"Lyria error: {e}")
            return None
```

9. Tools: Sentiment Analyzer (sentiment_analyzer.py)

```python
# src/tools/sentiment_analyzer.py
from google import genai
import os
from typing import Dict

class SentimentAnalyzerTool:
    """Analyze sentiment of script text."""
    
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        self.client = genai.Client(api_key=api_key)
    
    def analyze_sentiment(self, script_text: str) -> Dict:
        """Analyze tone and sentiment of script."""
        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash-exp",
                contents=f"""
                Analyze the sentiment and tone of this podcast script:
                {script_text[:5000]}
                
                Return JSON with:
                - overall_tone: (positive/neutral/negative)
                - emotional_arc: list of emotions throughout
                - speaker_tone: dict of speaker to tone
                - audience_engagement: rating 1-10
                - recommendations: list of suggestions
                """
            )
            
            return {
                "analysis": response.text,
                "overall_tone": "positive",  # Simplified
                "emotional_arc": ["intro", "build", "climax", "conclusion"],
                "speaker_tone": {},
                "audience_engagement": 8
            }
            
        except Exception as e:
            print(f"Sentiment error: {e}")
            return {"error": str(e)}
```

10. FastAPI Main Application (main.py)

```python
# src/main.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
import shutil
from src.phase4_adk_agents.orchestrator import PodcastOrchestrator
from src.config import Config

app = FastAPI(
    title="Podcast-to-Production Agent",
    description="Multi-agent system for automated podcast production",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestrator
orchestrator = PodcastOrchestrator()

# Models
class ScriptRequest(BaseModel):
    genre: Optional[str] = "general"

class ProcessResponse(BaseModel):
    status: str
    script_analysis: dict
    director_notes: dict
    market_research: dict
    audio_production: dict
    recommendations: list
    download_url: str

# Endpoints
@app.get("/")
async def root():
    return {"message": "Podcast-to-Production Agent API", "status": "running"}

@app.post("/upload")
async def upload_script(
    file: UploadFile = File(...),
    genre: str = "general"
):
    """Upload a podcast script PDF and start production."""
    try:
        # Validate file
        if not file.filename.endswith('.pdf'):
            raise HTTPException(400, "File must be a PDF")
        
        # Save file
        upload_path = os.path.join(Config.UPLOAD_DIR, file.filename)
        os.makedirs(Config.UPLOAD_DIR, exist_ok=True)
        
        with open(upload_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        # Process script
        result = orchestrator.process_script(upload_path, genre)
        
        return JSONResponse({
            "status": "success",
            "data": result,
            "message": "Podcast production complete!"
        })
        
    except Exception as e:
        raise HTTPException(500, str(e))

@app.post("/analyze")
async def analyze_script_only(
    file: UploadFile = File(...)
):
    """Analyze script without generating audio."""
    try:
        upload_path = os.path.join(Config.UPLOAD_DIR, file.filename)
        os.makedirs(Config.UPLOAD_DIR, exist_ok=True)
        
        with open(upload_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        # Parse only
        parser = PDFScriptParser()
        script_data = parser.parse(upload_path)
        
        return JSONResponse({
            "status": "success",
            "script_analysis": script_data,
            "message": "Script analysis complete"
        })
        
    except Exception as e:
        raise HTTPException(500, str(e))

@app.get("/download/{filename}")
async def download_file(filename: str):
    """Download generated audio files."""
    file_path = os.path.join(Config.OUTPUT_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type='audio/wav')
    raise HTTPException(404, "File not found")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "services": ["Gemini", "Parallel", "TTS", "Lyria"]}

# Run
if __name__ == "__main__":
    import uvicorn
    os.makedirs(Config.UPLOAD_DIR, exist_ok=True)
    os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

11. Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create directories
RUN mkdir -p uploads outputs static

# Expose port
EXPOSE 8000

# Run
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

12. docker-compose.yml

```yaml
version: '3.8'

services:
  podcast-agent:
    build: .
    container_name: podcast-production-agent
    ports:
      - "8000:8000"
    environment:
      - GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - PARALLEL_API_KEY=${PARALLEL_API_KEY}
      - LYRIA_API_KEY=${LYRIA_API_KEY}
      - GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json
    volumes:
      - ./uploads:/app/uploads
      - ./outputs:/app/outputs
      - ./credentials.json:/app/credentials.json:ro
    restart: unless-stopped
```

13. README.md

```markdown
# 🎙️ Podcast-to-Production Agent

## Google Cloud Agentic Cinema Hackathon Submission

### Overview
A multi-agent system that converts podcast scripts into complete, production-ready audio episodes in minutes.

### Features
- 📄 **PDF Script Parsing** - Extract structured data from scripts
- 🎬 **Director Agent** - Analyze structure, tone, and pacing
- 🔍 **Researcher Agent** - Market intelligence via Parallel Search
- 🎵 **Audio Producer Agent** - TTS + Music + Sentiment Analysis
- 🎤 **Multi-Speaker TTS** - Different voices for each speaker
- 🎼 **Background Music** - Mood-matched via Lyria 3
- 📊 **Sentiment Analysis** - Compare script tone vs. audio

### Tech Stack
- **Gemini Enterprise** - Primary AI engine
- **Agent Engine (ADK)** - Multi-agent orchestration
- **Parallel Search** - Web intelligence
- **Gemini TTS** - Speech generation
- **Lyria 3** - Music generation
- **Cloud Run** - Deployment
- **FastAPI** - API framework

### Setup Instructions
1. **Clone the repository**
2. **Add API keys to .env**
3. **Run with Docker:**
   ```bash
   docker-compose up --build
```

4. Access API at: http://localhost:8000

API Endpoints

· POST /upload - Upload script PDF
· POST /analyze - Analyze only (no audio)
· GET /download/{filename} - Download audio
· GET /health - Health check

Demo Video

[Link to YouTube/Video]

License

Apache 2.0

This project was built with [Lovable](https://lovable.dev).

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/85fe6aba-2c82-4c3b-be60-e22ac4c911ae).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
