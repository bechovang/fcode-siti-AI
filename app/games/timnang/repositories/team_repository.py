"""
Repository for accessing team data.
"""

from typing import List, Optional
from schemas.timnang import Team
import timnang_data as data_source


class TeamRepository:
    """Repository for accessing team data from timnang_data.py."""

    def __init__(self):
        """Initialize repository with data source."""
        self._teams = data_source.TEAMS

    def get_all(self) -> List[Team]:
        """
        Get all teams.

        Returns:
            List of all 3 teams
        """
        return self._teams

    def get_by_id(self, team_id: str) -> Optional[Team]:
        """
        Get team by ID.

        Args:
            team_id: Team ID ("A", "B", or "C")

        Returns:
            Team or None if not found
        """
        for team in self._teams:
            if team.id == team_id:
                return team
        return None

    def team_exists(self, team_id: str) -> bool:
        """
        Check if team exists.

        Args:
            team_id: Team ID to check

        Returns:
            True if team exists, False otherwise
        """
        return self.get_by_id(team_id) is not None

    def get_team_ids(self) -> List[str]:
        """
        Get all team IDs in order.

        Returns:
            List of team IDs ["A", "B", "C"]
        """
        return [team.id for team in self._teams]

    def count(self) -> int:
        """
        Get total number of teams.

        Returns:
            Number of teams (always 3)
        """
        return len(self._teams)
