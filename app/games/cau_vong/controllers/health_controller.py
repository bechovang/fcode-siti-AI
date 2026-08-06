"""
Health check controller for Cầu Vồng.
"""

from fastapi import Response
from typing import Optional, Any


class HealthController:
    """Controller for health check endpoint."""

    def __init__(self, llm: Optional[Any], model: Optional[str], live2d_available: bool):
        """
        Initialize health controller.

        Args:
            llm: LLM client (optional - may be None if no API key)
            model: Model name (optional)
            live2d_available: Whether Live2D models are available
        """
        self.llm = llm
        self.model = model
        self.live2d_available = live2d_available

    async def get_health(self) -> dict:
        """
        Get health status.

        Returns:
            Health status dictionary
        """
        return {
            "ok": True,
            "tts": True,  # Always True after warmup
            "tts_voice": "mai_linh",
            "tts_model": "Kokoro-Vietnamese (ONNX CPU)",
            "stt": "browser (Web Speech API)",
            "llm": self.llm is not None,
            "llm_model": self.model if self.llm else None,
            "live2d": self.live2d_available
        }
