"""
Repository for accessing script/narrative data.
"""

from typing import List, Tuple
import koon_data as data_source


class ScriptRepository:
    """Repository for accessing script and narrative data from koon_data.py."""

    def __init__(self):
        """Initialize repository with data source."""
        self._intro = data_source.INTRO
        self._recap = data_source.RECAP
        self._goodbye = data_source.GOODBYE
        self._intro_lines = data_source.INTRO_LINES
        self._outro_recap = data_source.OUTRO_RECAP
        self._magic_line = data_source.MAGIC_LINE
        self._outro_goodbye = data_source.OUTRO_GOODBYE

    def get_intro_keys(self) -> List[str]:
        """
        Get intro audio keys in order.

        Returns:
            List of audio keys for intro sequence
        """
        return self._intro

    def get_recap_key(self) -> str:
        """
        Get recap audio key.

        Returns:
            Audio key for recap
        """
        return self._recap

    def get_goodbye_key(self) -> str:
        """
        Get goodbye audio key.

        Returns:
            Audio key for goodbye
        """
        return self._goodbye

    def get_intro_lines(self) -> List[str]:
        """
        Get intro narration lines (for dynamic TTS).

        Returns:
            List of intro narration lines
        """
        return self._intro_lines

    def get_outro_recap(self) -> str:
        """
        Get outro recap narration text.

        Returns:
            Outro recap text for TTS
        """
        return self._outro_recap

    def get_magic_line(self) -> str:
        """
        Get magic line narration text.

        Returns:
            Magic line text for TTS
        """
        return self._magic_line

    def get_outro_goodbye(self) -> str:
        """
        Get outro goodbye narration text.

        Returns:
            Outro goodbye text for TTS
        """
        return self._outro_goodbye

    def get_audio_dir(self) -> str:
        """
        Get audio directory path.

        Returns:
            Path to koon audio directory
        """
        return data_source.AUDIO_DIR

    def get_video_dir(self) -> str:
        """
        Get video directory path.

        Returns:
            Path to video directory
        """
        return data_source.VIDEO_DIR

    def get_recap_video_path(self) -> str:
        """
        Get recap video path.

        Returns:
            Path to recap video file
        """
        return data_source.RECAP_VIDEO
