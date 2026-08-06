"""
Repository for accessing challenge data.
"""

from typing import List, Optional
from schemas.cau_vong import Challenge
import koon_data as data_source


class ChallengeRepository:
    """Repository for accessing challenge data from koon_data.py."""

    def __init__(self):
        """Initialize repository with data source."""
        self._challenges = data_source.CHALLENGES

    def get_all(self) -> List[Challenge]:
        """
        Get all challenges.

        Returns:
            List of all 7 challenges
        """
        return self._challenges

    def get_by_index(self, idx: int) -> Optional[Challenge]:
        """
        Get challenge by index.

        Args:
            idx: Challenge index (0-6)

        Returns:
            Challenge at index or None if out of range
        """
        if 0 <= idx < len(self._challenges):
            return self._challenges[idx]
        return None

    def get_rainbow_hexes(self) -> List[str]:
        """
        Get all rainbow hex colors in order.

        Returns:
            List of hex color codes
        """
        return data_source.RAINBOW_HEX

    def count(self) -> int:
        """
        Get total number of challenges.

        Returns:
            Number of challenges (always 7)
        """
        return len(self._challenges)
