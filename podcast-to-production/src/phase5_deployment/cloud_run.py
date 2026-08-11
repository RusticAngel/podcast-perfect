"""Cloud Run deployment configuration helpers."""

import os
from typing import Dict, List

from src.config import Config

SERVICE_NAME = os.getenv("CLOUD_RUN_SERVICE", "podcast-to-production")
REGION = os.getenv("CLOUD_RUN_REGION", "us-central1")


def service_config() -> Dict:
    """Return the Cloud Run service configuration used for deployment."""
    return {
        "service": SERVICE_NAME,
        "region": REGION,
        "project": Config.PROJECT_ID,
        "cpu": "2",
        "memory": "4Gi",
        "timeout": "900s",
        "concurrency": 4,
        "min_instances": 0,
        "max_instances": 10,
        "port": 8000,
        "allow_unauthenticated": True,
        "env_vars": [
            "GOOGLE_CLOUD_PROJECT",
            "GEMINI_API_KEY",
            "GEMINI_MODEL",
            "PARALLEL_API_KEY",
            "LYRIA_API_KEY",
            "DEFAULT_TTS_VOICE",
            "SECONDARY_TTS_VOICE",
        ],
    }


def deploy_command() -> List[str]:
    """gcloud command to deploy this service to Cloud Run."""
    cfg = service_config()
    secrets = ",".join(f"{name}={name}:latest" for name in cfg["env_vars"] if "KEY" in name)
    return [
        "gcloud", "run", "deploy", cfg["service"],
        "--source", ".",
        "--project", str(cfg["project"]),
        "--region", cfg["region"],
        "--cpu", cfg["cpu"],
        "--memory", cfg["memory"],
        "--timeout", cfg["timeout"],
        "--concurrency", str(cfg["concurrency"]),
        "--max-instances", str(cfg["max_instances"]),
        "--port", str(cfg["port"]),
        "--allow-unauthenticated",
        "--set-secrets", secrets,
        "--set-env-vars", f"GOOGLE_CLOUD_PROJECT={cfg['project']}",
    ]


if __name__ == "__main__":
    print(" ".join(deploy_command()))
