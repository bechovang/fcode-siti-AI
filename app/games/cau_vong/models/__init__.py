"""
Models for Cầu Vồng (Game 1).
Models represent domain state and data structures.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from schemas.cau_vong import Game1Phase


@dataclass
class SessionState:
    """State management for game session."""

    phase: Game1Phase = Game1Phase.IDLE
    challenge_index: int = 0
    unlocked_colors: list[str] = None
    events: Dict[str, Any] = None

    def __post_init__(self):
        if self.unlocked_colors is None:
            self.unlocked_colors = []
        if self.events is None:
            self.events = {
                "_audio_done": None,
                "_answer_ready": None,
                "_video_done": None
            }

    def reset(self):
        """Reset session to initial state."""
        self.phase = Game1Phase.IDLE
        self.challenge_index = 0
        self.unlocked_colors = []
        self.events = {
            "_audio_done": None,
            "_answer_ready": None,
            "_video_done": None
        }
