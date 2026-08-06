"""
Models for Tìm Nắng (Game 2).
Models represent domain state and data structures.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
from schemas.timnang import Game2Phase, TeamState


@dataclass
class GameState:
    """State management for game."""

    phase: Game2Phase = Game2Phase.IDLE
    round_idx: int = 0
    current_object: Optional[str] = None
    teams: Dict[str, TeamState] = field(default_factory=dict)

    def reset(self):
        """Reset game to initial state."""
        self.phase = Game2Phase.IDLE
        self.round_idx = 0
        self.current_object = None
        for team_state in self.teams.values():
            team_state["score"] = 0
            team_state["order"] = None
