"""
Repository for accessing script/text builder data.
"""

from typing import Dict, Callable
from schemas.timnang import GameObject
import timnang_data as data_source


class ScriptRepository:
    """Repository for accessing script and text builder data from timnang_data.py."""

    def __init__(self):
        """Initialize repository with data source."""
        self._intro_text = data_source.INTRO_TEXT
        self._score_by_order = data_source.SCORE_BY_ORDER
        self._round_text = data_source.round_text
        self._correct_text = data_source.correct_text
        self._num_vi = data_source.num_vi
        self._precache_lines = data_source.precache_lines

    def get_intro_text(self) -> str:
        """
        Get intro narration text.

        Returns:
            Intro text for TTS
        """
        return self._intro_text

    def get_score_by_order(self) -> list:
        """
        Get scoring array by order.

        Returns:
            List of points [3, 2, 1] for 1st/2nd/3rd place
        """
        return self._score_by_order

    def get_round_text(self, idx: int, obj: GameObject) -> str:
        """
        Get round announcement text.

        Args:
            idx: Round index (0-5)
            obj: GameObject for this round

        Returns:
            Round announcement text
        """
        return self._round_text(idx, obj)

    def get_correct_text(self, team_name: str, order: int) -> str:
        """
        Get correct answer announcement text.

        Args:
            team_name: Name of team that got it right
            order: Finish order (1, 2, or 3)

        Returns:
            Correct announcement text
        """
        return self._correct_text(team_name, order)

    def num_vi(self, n: int) -> str:
        """
        Convert number to Vietnamese text.

        Args:
            n: Number to convert (0-18)

        Returns:
            Vietnamese text representation
        """
        return self._num_vi(n)

    def get_precache_lines(self) -> Dict[str, str]:
        """
        Get all pre-cache TTS lines.

        Returns:
            Dictionary of audio keys to text lines
        """
        return self._precache_lines()

    def get_audio_dir(self) -> str:
        """
        Get audio directory path.

        Returns:
            Path to timnang audio directory
        """
        return data_source.AUDIO_DIR

    def get_static_dir(self) -> str:
        """
        Get static directory path.

        Returns:
            Path to timnang static directory
        """
        return data_source.STATIC_DIR

    def get_rounds_count(self) -> int:
        """
        Get total number of rounds.

        Returns:
            Number of rounds (always 6)
        """
        return data_source.ROUNDS
