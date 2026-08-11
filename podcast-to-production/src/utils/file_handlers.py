"""File upload/download utilities."""

import os
import re
import shutil
import uuid
from typing import BinaryIO

from src.config import Config

SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]")
MAX_UPLOAD_BYTES = 25 * 1024 * 1024


def ensure_dirs() -> None:
    for directory in (Config.UPLOAD_DIR, Config.OUTPUT_DIR, Config.STATIC_DIR):
        os.makedirs(directory, exist_ok=True)


def sanitize_filename(filename: str) -> str:
    base = os.path.basename(filename or "upload.pdf")
    return SAFE_NAME.sub("_", base) or "upload.pdf"


def save_upload(file_obj: BinaryIO, filename: str) -> str:
    """Persist an uploaded file under a unique, sanitized name."""
    ensure_dirs()
    safe = sanitize_filename(filename)
    unique = f"{uuid.uuid4().hex[:8]}_{safe}"
    path = os.path.join(Config.UPLOAD_DIR, unique)
    with open(path, "wb") as handle:
        shutil.copyfileobj(file_obj, handle)
    return path


def resolve_output_path(filename: str) -> str:
    """Resolve a filename inside the output dir, blocking path traversal."""
    ensure_dirs()
    safe = sanitize_filename(filename)
    root = os.path.realpath(Config.OUTPUT_DIR)
    path = os.path.realpath(os.path.join(root, safe))
    if not path.startswith(root + os.sep):
        raise ValueError("Invalid filename")
    return path


def cleanup(path: str) -> None:
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except OSError:
        pass
