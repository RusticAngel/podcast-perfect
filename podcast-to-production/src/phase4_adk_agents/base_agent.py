"""Abstract base class for all ADK / Agent Engine agents."""

import os
from abc import ABC, abstractmethod
from typing import Any

try:  # pragma: no cover - Vertex AI is optional in local/demo runs
    from google.cloud import aiplatform
    from vertexai.preview import reasoning_engines
except ImportError:  # pragma: no cover
    aiplatform = None
    reasoning_engines = None


class BaseAgent(ABC):
    """Abstract base class for all ADK agents."""

    def __init__(self, model_name: str = "gemini-2.0-flash-exp"):
        self.model_name = model_name
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

        # Initialize Vertex AI / Agent Engine when credentials are available.
        self.vertex_ready = False
        if aiplatform is not None and self.project_id:
            try:
                aiplatform.init(project=self.project_id, location=self.location)
                self.vertex_ready = True
            except Exception as exc:  # noqa: BLE001
                print(f"Vertex AI unavailable, using AI gateway: {exc}")

    @abstractmethod
    def create_agent(self) -> "reasoning_engines.ReasoningEngine":
        """Create and return the ADK agent instance."""

    @abstractmethod
    def run(self, input_data: Any) -> Any:
        """Run the agent with given input."""
