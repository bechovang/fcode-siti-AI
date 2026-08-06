"""
Health check controller for Tìm Nắng.
"""

from typing import Optional, Any, List


class HealthController:
    """Controller for health check endpoint."""

    def __init__(self, llm: Optional[Any], model: Optional[str], teams: List[str], num_objects: int):
        """
        Initialize health controller.

        Args:
            llm: LLM client (optional - may be None if no API key)
            model: Model name (optional)
            teams: List of team names
            num_objects: Number of game objects
        """
        self.llm = llm
        self.model = model
        self.teams = teams
        self.num_objects = num_objects

    async def get_health(self) -> dict:
        """
        Get health status.

        Returns:
            Health status dictionary
        """
        return {
            "ok": True,
            "game": "timnang",
            "tts": True,  # Always True after warmup
            "tts_voice": "mai_linh",
            "vision": self.llm is not None,
            "vision_model": self.model if self.llm else None,
            "teams": self.teams,
            "objects": self.num_objects,
            "rounds": 6
        }
