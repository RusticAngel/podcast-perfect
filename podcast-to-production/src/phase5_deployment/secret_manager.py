"""Secure API key management via Google Secret Manager."""

import os
from functools import lru_cache
from typing import Optional

from src.config import Config

try:  # pragma: no cover - optional at import time
    from google.cloud import secretmanager
except ImportError:  # pragma: no cover
    secretmanager = None


@lru_cache(maxsize=1)
def _client():
    if secretmanager is None:
        return None
    try:
        return secretmanager.SecretManagerServiceClient()
    except Exception:  # noqa: BLE001
        return None


def get_secret(name: str, version: str = "latest") -> Optional[str]:
    """Read a secret, preferring the environment and falling back to Secret Manager."""
    env_value = os.getenv(name)
    if env_value:
        return env_value

    client = _client()
    project = Config.PROJECT_ID
    if client is None or not project:
        return None

    try:
        path = f"projects/{project}/secrets/{name}/versions/{version}"
        response = client.access_secret_version(request={"name": path})
        return response.payload.data.decode("utf-8")
    except Exception as exc:  # noqa: BLE001
        print(f"Secret Manager error for {name}: {exc}")
        return None


def hydrate_environment(names: Optional[list] = None) -> dict:
    """Load required secrets into os.environ at startup."""
    names = names or [
        "GEMINI_API_KEY",
        "PARALLEL_API_KEY",
        "LYRIA_API_KEY",
    ]
    loaded = {}
    for name in names:
        value = get_secret(name)
        if value:
            os.environ[name] = value
        loaded[name] = bool(value)
    return loaded
