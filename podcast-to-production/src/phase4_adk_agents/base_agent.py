"""Abstract base class for all ADK / Agent Engine agents."""

import os
from abc import ABC, abstractmethod
from typing import Any

from google.cloud import aiplatform
from vertexai.preview import reasoning_engines


class BaseAgent(ABC):
    """Abstract base class for all ADK agents."""

    def __init__(self, model_name: str = "gemini-2.0-flash-exp"):
        self.model_name = model_name
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

        # Initialize Vertex AI / Agent Engine
        aiplatform.init(project=self.project_id, location=self.location)

    @abstractmethod
    def create_agent(self) -> "reasoning_engines.ReasoningEngine":
        """Create and return the ADK agent instance."""

    @abstractmethod
    def run(self, input_data: Any) -> Any:
        """Run the agent with given input."""
