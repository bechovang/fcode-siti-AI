"""
Service for game state management.
"""

import asyncio
import logging
from typing import Dict, Optional

from schemas.timnang import Game2Phase, Team, TeamState
from games.timnang.models import GameState

log = logging.getLogger("timnang.state")


class GameStateService:
    """Service for managing game state and phase transitions."""

    def __init__(self, teams: list[Team]):
        """
        Initialize game state service.

        Args:
            teams: List of teams (from TeamRepository)
        """
        self.state = GameState()
        self.lock = asyncio.Lock()

        # Initialize teams
        for team in teams:
            self.state.teams[team.id] = {
                "name": team.name,
                "color": team.color,
                "score": 0,
                "order": None,
                "last_rec": 0.0
            }

    async def reset(self):
        """Reset game to initial state."""
        async with self.lock:
            self.state.reset()
            for team_state in self.state.teams.values():
                team_state["score"] = 0
                team_state["order"] = None
                team_state["last_rec"] = 0.0

    async def transition_to_announce(self) -> bool:
        """Transition to ANNOUNCE phase."""
        async with self.lock:
            if self.state.phase != Game2Phase.IDLE:
                return False
            self.state.phase = Game2Phase.ANNOUNCE
            self.state.round_idx = -1
            return True

    async def transition_to_playing(self, round_idx: int, object_id: str) -> bool:
        """Transition to PLAYING phase for new round."""
        async with self.lock:
            if self.state.phase != Game2Phase.ANNOUNCE:
                return False
            self.state.phase = Game2Phase.PLAYING
            self.state.round_idx = round_idx
            self.state.current_object = object_id

            # Reset team orders for new round
            for team_state in self.state.teams.values():
                team_state["order"] = None
                team_state["last_rec"] = 0.0
            return True

    async def transition_to_round_end(self) -> bool:
        """Transition to ROUND_END phase."""
        async with self.lock:
            if self.state.phase not in (Game2Phase.PLAYING, Game2Phase.ANNOUNCE):
                return False
            self.state.phase = Game2Phase.ROUND_END
            return True

    async def transition_to_game_over(self) -> bool:
        """Transition to GAME_OVER phase."""
        async with self.lock:
            if self.state.phase != Game2Phase.ROUND_END:
                return False
            self.state.phase = Game2Phase.GAME_OVER
            return True

    def is_round_complete(self) -> bool:
        """Check if current round is complete (all teams finished)."""
        return all(
            team_state["order"] is not None
            for team_state in self.state.teams.values()
        )

    def has_more_rounds(self, total_rounds: int) -> bool:
        """Check if there are more rounds to play."""
        return self.state.round_idx + 1 < total_rounds

    def get_team_state(self, team_id: str) -> Optional[TeamState]:
        """Get state for specific team."""
        return self.state.teams.get(team_id)

    def get_all_teams(self) -> Dict[str, TeamState]:
        """Get all team states."""
        return self.state.teams.copy()

    def get_phase(self) -> Game2Phase:
        """Get current game phase."""
        return self.state.phase

    def get_round_index(self) -> int:
        """Get current round index."""
        return self.state.round_idx

    def get_current_object_id(self) -> Optional[str]:
        """Get current game object ID."""
        return self.state.current_object

    async def update_team_score(self, team_id: str, delta: int) -> bool:
        """Update team score by delta (clamped ±10)."""
        async with self.lock:
            if team_id not in self.state.teams:
                return False

            # Coerce + clamp: trust boundary protection
            try:
                delta = int(delta)
            except (TypeError, ValueError):
                log.warning("update_team_score delta không hợp lệ: %r — bỏ qua", delta)
                return False

            if abs(delta) > 10:
                delta = max(-10, min(10, delta))
                log.warning("update_team_score delta clamp ±10 → %d", delta)

            self.state.teams[team_id]["score"] += delta
            return True

    def get_ranking(self) -> list:
        """Get ranking of teams by score (highest first)."""
        return sorted(
            [
                {"id": tid, "name": t["name"], "color": t["color"], "score": t["score"]}
                for tid, t in self.state.teams.items()
            ],
            key=lambda r: r["score"],
            reverse=True,
        )

    async def acquire_lock(self):
        """Acquire state lock for atomic operations."""
        await self.lock.acquire()

    def release_lock(self):
        """Release state lock."""
        self.lock.release()
