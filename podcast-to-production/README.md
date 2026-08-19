# Podcast-to-Production Agent

**Google Cloud Agentic Cinema Hackathon submission** — a multi-agent system that turns a podcast script or interview transcript (PDF) into a production-ready episode in minutes.

## Overview

Podcast production takes 5–10 hours per episode: scripting, recording, editing, music, mastering. This agent compresses that to ~5 minutes by orchestrating three specialised Google Cloud agents over a parsed script.

## Features

- **PDF script parsing** — speakers, dialogue segments, topics, mood, scene breaks, duration estimate
- **Director Agent** — structure, tone, pacing and production cues (Gemini on Agent Engine)
- **Researcher Agent** — market intelligence via the Parallel Search API
- **Audio Producer Agent** — multi-speaker Gemini TTS, Lyria 3 music beds, sentiment analysis
- **Multimodal sentiment QA** — compares intended script tone vs. delivered audio tone
- **Production readiness report** — actionable recommendations and mix notes

## Tech Stack

| Layer | Technology |
| --- | --- |
| Agent reasoning | Gemini Enterprise via `google-genai` |
| Orchestration | Google Cloud Agent Engine (`aiplatform[agent_engines,adk]`) |
| Speech | Gemini TTS (multi-speaker) |
| Music | Lyria 3 on Vertex AI |
| Web intelligence | Parallel Search API (partner integration) |
| API | FastAPI + Uvicorn |
| Deployment | Cloud Run + Secret Manager |

## Architecture

```text
PDF script
    |
    v
Phase 2  parse -> speakers, segments, topics, mood
    |
    v
Phase 4  Orchestrator
    |-- Director Agent    (Gemini)            -> structure, tone, pacing
    |-- Researcher Agent  (Gemini + Parallel) -> market intelligence
    +-- Audio Producer    (Gemini TTS + Lyria)-> speech, music, sentiment
    |
    v
Production report + downloadable audio assets
```

## Project Layout

```text
src/
  phase2_document_processing/  pdf_parser, speaker_identifier, script_analyzer
  phase3_partner_integration/  parallel_search
  phase4_adk_agents/           base, director, researcher, audio_producer, orchestrator
  phase5_deployment/           cloud_run, secret_manager
  tools/                       gemini_tts, lyria_music, sentiment_analyzer, audio_utils
  models/                      schemas
  utils/                       file_handlers
tests/                         parser, partner API, agent tests
notebooks/                     agent_test.ipynb
static/                        demo_script.pdf
```

## Setup

1. Clone the repository.
2. Copy `.env.example` to `.env` and fill in your keys.
3. Run with Docker:

```bash
docker-compose up --build
```

Or locally:

```bash
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000
```

4. Open http://localhost:8000/docs

## API Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | Demo front-end: upload a PDF, watch progress, download artifacts |
| `POST` | `/upload` | Upload a script PDF and run the full production pipeline |
| `POST` | `/analyze` | Parse and analyse a script without generating audio |
| `GET` | `/download/{filename}` | Download a generated audio asset |
| `GET` | `/health` | Service health check |

Quick demo:

```bash
curl -F "file=@static/demo_script.pdf" "http://localhost:8000/upload?genre=technology"
```

## Tests

```bash
pytest tests -v
```

Tests run fully offline — cloud clients are stubbed.

## Deployment

```bash
python -m src.phase5_deployment.cloud_run   # prints the gcloud deploy command
```

Secrets (`GEMINI_API_KEY`, `PARALLEL_API_KEY`, `LYRIA_API_KEY`) are read from Google Secret Manager at startup, with environment variables taking precedence for local development.

## Demo Video

[Link to YouTube/Video]

## License

Apache 2.0 — see [LICENSE](./LICENSE).
