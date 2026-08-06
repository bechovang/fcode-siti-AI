"""
Service for TTS (Text-to-Speech) synthesis and audio playback.
"""

import asyncio
import logging
import os
from typing import Optional

from core import tts
from games.timnang.services.broadcast_service import BroadcastService

log = logging.getLogger("timnang.tts")


class TTSService:
    """Service for TTS orchestration and audio playback (master only)."""

    def __init__(self, tts_dir: str, audio_dir: str, broadcast: BroadcastService):
        """
        Initialize TTS service.

        Args:
            tts_dir: Directory for temporary TTS files
            audio_dir: Directory for pre-cached audio files
            broadcast: Broadcast service for sending audio to masters
        """
        self.tts_dir = tts_dir
        self.audio_dir = audio_dir
        self.broadcast = broadcast

    async def say(self, text: str):
        """
        Synthesize text to TTS and broadcast to masters.

        Args:
            text: Text to synthesize
        """
        result = await tts.synthesize_to_temp_wav(text, self.tts_dir)
        if result is None:
            return

        key, _wav_path = result
        await self.broadcast.broadcast_masters({"type": "play_audio", "key": key})
        # Note: Don't cleanup temp file immediately - let /audio endpoint serve it
        # Cleanup can be done periodically if needed

    async def play_audio(self, key: str):
        """
        Play pre-cached audio file to masters.

        Args:
            key: Audio key (without .wav/.mp3 extension)
        """
        await self.broadcast.broadcast_masters({"type": "play_audio", "key": key})

    async def play_or_say(self, key: str, text: str):
        """
        Play pre-cached audio if available, otherwise synthesize dynamically.

        Args:
            key: Pre-cached audio key
            text: Fallback text for dynamic TTS
        """
        wav = os.path.join(self.audio_dir, f"{key}.wav")
        mp3 = os.path.join(self.audio_dir, f"{key}.mp3")

        if os.path.isfile(wav) or os.path.isfile(mp3):
            await self.play_audio(key)
        else:
            await self.say(text)

    def stop_audio(self):
        """Stop all audio playback."""
        asyncio.create_task(self.broadcast.broadcast_masters({"type": "stop_audio"}))

    def get_precached_path(self, key: str) -> str:
        """
        Get full path to pre-cached audio file.

        Args:
            key: Audio key (without extension)

        Returns:
            Full path to audio file (wav or mp3)
        """
        wav = os.path.join(self.audio_dir, f"{key}.wav")
        if os.path.isfile(wav):
            return wav

        mp3 = os.path.join(self.audio_dir, f"{key}.mp3")
        return mp3

    def has_precached(self, key: str) -> bool:
        """
        Check if pre-cached audio file exists.

        Args:
            key: Audio key

        Returns:
            True if pre-cached file exists
        """
        return os.path.isfile(self.get_precached_path(key))
