"""
Service for scoring and team ordering logic.
"""

import logging
from typing import Tuple, Optional

from schemas.timnang import Game2Phase
from games.timnang.services.game_state_service import GameStateService
from games.timnang.repositories.script_repository import ScriptRepository

log = logging.getLogger("timnang.scoring")


class ScoringService:
    """Service for scoring logic and order assignment."""

    def __init__(
        self,
        game_state: GameStateService,
        script_repo: ScriptRepository,
    ):
        """
        Initialize scoring service.

        Args:
            game_state: Game state service
            script_repo: Script repository for scoring rules
        """
        self.game_state = game_state
        self.script_repo = script_repo

    async def assign_order(
        self,
        team_id: str,
        correct_label: str = "Đúng rồi!"
    ) -> Tuple[bool, Optional[int], Optional[int]]:
        """
        Assign order + points to team if not yet finished (atomic).

        Args:
            team_id: Team ID to assign order
            correct_label: Label for TTS ("Đúng rồi!" / "Đã duyệt!")

        Returns:
            Tuple of (success, order, points)
            - success: True if assigned, False if already finished/invalid
            - order: Order (1, 2, 3) if successful, None otherwise
            - points: Points assigned if successful, None otherwise
        """
        teams = self.game_state.get_all_teams()
        if team_id not in teams:
            return False, None, None

        async with self.game_state.lock:
            # Re-check conditions under lock (prevent double-score race)
            if self.game_state.get_phase() != Game2Phase.PLAYING:
                return False, None, None

            team_state = teams[team_id]
            if team_state["order"] is not None:
                return False, None, None  # Already finished this round

            # Calculate order (1-based index of finishers + 1)
            order = sum(1 for t in teams.values() if t["order"] is not None) + 1

            # Get points from scoring rules
            score_by_order = self.script_repo.get_score_by_order()
            points = score_by_order[order - 1] if order <= len(score_by_order) else 0

            # Update team state
            team_state["order"] = order
            team_state["score"] += points

        log.info("[%s] về %d (+%d pts)", team_id, order, points)
        return True, order, points

    async def force_accept(self, team_id: str) -> Tuple[bool, Optional[int], Optional[int]]:
        """
        Operator force-accept for team (bypass vision).

        Args:
            team_id: Team ID to force accept

        Returns:
            Tuple of (success, order, points)
        """
        return await self.assign_order(team_id, correct_label="Đã duyệt!")

    def can_recognize(self, team_id: str, debounce_seconds: float) -> Tuple[bool, Optional[str]]:
        """
        Check if team can recognize (debounce + not finished).

        Args:
            team_id: Team ID to check
            debounce_seconds: Debounce period in seconds

        Returns:
            Tuple of (allowed, error_message)
            - allowed: True if can recognize
            - error_message: Error message if not allowed
        """
        import time

        teams = self.game_state.get_all_teams()
        if team_id not in teams:
            return False, "Đội không tồn tại"

        if self.game_state.get_phase() != Game2Phase.PLAYING:
            return False, "Chờ vòng bắt đầu nhé!"

        team_state = teams[team_id]
        if team_state["order"] is not None:
            return False, "Đã về đích vòng này rồi"

        now = time.time()
        if now - team_state["last_rec"] < debounce_seconds:
            return False, "Chờ một chút rồi bấm lại nhé!"

        # Update last recognition time
        team_state["last_rec"] = now
        return True, None
