import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Google Cloud
    PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")
    CREDENTIALS_PATH = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

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
