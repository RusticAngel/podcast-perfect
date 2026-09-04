"""FastAPI application for the Podcast-to-Production Agent."""

import json
import os
from typing import Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from src.config import Config
from src.models.schemas import HealthResponse
from src.phase2_document_processing.pdf_parser import PDFScriptParser
from src.phase2_document_processing.script_analyzer import ScriptAnalyzer
from src.phase2_document_processing.speaker_identifier import SpeakerIdentifier
from src.tools import audio_utils
from src.utils.file_handlers import ensure_dirs, resolve_output_path, save_upload

app = FastAPI(
    title="Podcast-to-Production Agent",
    description="Multi-agent system for automated podcast production",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_orchestrator = None


def get_orchestrator():
    """Lazily construct the orchestrator so the API boots without cloud creds."""
    global _orchestrator
    if _orchestrator is None:
        from src.phase4_adk_agents.orchestrator import PodcastOrchestrator

        _orchestrator = PodcastOrchestrator()
    return _orchestrator


@app.on_event("startup")
async def startup() -> None:
    ensure_dirs()


@app.get("/")
async def root():
    """Serve the demo front-end (falls back to JSON if the page is missing)."""
    demo_page = os.path.join(Config.STATIC_DIR, "demo.html")
    if os.path.exists(demo_page):
        return FileResponse(demo_page, media_type="text/html")
    return {"message": "Podcast-to-Production Agent API", "status": "running"}


@app.post("/upload")
async def upload_script(
    file: UploadFile = File(...),
    genre: str = "general",
    music_mood: str = "auto",
    music_intensity: float = 0.6,
    duck_db: float = -18.0,
    voice_map: str = "",
    render_video: bool = True,
    video_captions: bool = True,
):
    """Upload a podcast script PDF and start production."""
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(400, "File must be a PDF")

    upload_path = save_upload(file.file, file.filename)

    try:
        music_intensity = min(max(music_intensity, 0.05), 1.0)
        duck_db = min(max(duck_db, -40.0), 0.0)
        voices = {}
        if voice_map:
            try:
                parsed = json.loads(voice_map)
                if isinstance(parsed, dict):
                    voices = {
                        str(k): str(v) for k, v in parsed.items() if k and v and v != "auto"
                    }
            except json.JSONDecodeError as exc:
                raise HTTPException(400, "voice_map must be valid JSON") from exc
        result = get_orchestrator().process_script(
            upload_path,
            genre,
            music_mood=music_mood,
            music_intensity=music_intensity,
            voice_map=voices,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f"Production failed: {exc}") from exc

    production = result.get("audio_production", {})
    music_path: Optional[str] = production.get("music_path")

    # Stitch the speech clips and duck the music bed under the dialogue.
    clips = [f["audio_path"] for f in production.get("audio_files", []) if f.get("audio_path")]
    base = os.path.splitext(os.path.basename(upload_path))[0]
    dialogue_path = audio_utils.concatenate(
        clips, os.path.join(Config.OUTPUT_DIR, f"{base}_dialogue.wav")
    )
    final_path = None
    if dialogue_path:
        final_path = audio_utils.mix_with_music(
            dialogue_path,
            music_path or "",
            os.path.join(Config.OUTPUT_DIR, f"{base}_final_episode.wav"),
            music_gain_db=duck_db,
        )
        production["music_ducking_db"] = duck_db
        production["dialogue_track"] = dialogue_path
        production["final_episode"] = final_path
        production["final_duration_seconds"] = audio_utils.duration_seconds(
            final_path or dialogue_path
        )

    primary = final_path or music_path
    download_url = f"/download/{os.path.basename(primary)}" if primary else None

    return JSONResponse({
        "status": "success",
        "data": result,
        "download_url": download_url,
        "music_url": f"/download/{os.path.basename(music_path)}" if music_path else None,
        "message": "Podcast production complete!",
    })


@app.post("/analyze")
async def analyze_script_only(file: UploadFile = File(...)):
    """Analyze script without generating audio."""
    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(400, "File must be a PDF")

    upload_path = save_upload(file.file, file.filename)

    try:
        parser = PDFScriptParser()
        script_data = parser.parse(upload_path)
        script_data["speaker_profiles"] = SpeakerIdentifier().identify(
            script_data.get("dialogue_segments", [])
        )
        script_data["structural_analysis"] = ScriptAnalyzer().analyze(script_data)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(500, f"Analysis failed: {exc}") from exc

    return JSONResponse({
        "status": "success",
        "script_analysis": script_data,
        "message": "Script analysis complete",
    })


@app.get("/download/{filename}")
async def download_file(filename: str):
    """Download generated audio files."""
    try:
        file_path = resolve_output_path(filename)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="audio/wav", filename=filename)
    raise HTTPException(404, "File not found")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return {
        "status": "healthy",
        "services": ["Gemini", "Agent Engine", "Parallel Search", "Gemini TTS", "Lyria 3"],
    }


if __name__ == "__main__":
    import uvicorn

    ensure_dirs()
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))
