"""
Service for TTS (Text-to-Speech) synthesis and audio playback.
"""

import asyncio
import logging
import os
from typing import Optional, Tuple, Any

from core import tts
from fastapi import WebSocket

log = logging.getLogger("koon.tts")


class TTSService:
    """Service for TTS orchestration and audio playback."""

    def __init__(self, tts_dir: str, audio_dir: str):
        """
        Initialize TTS service.

        Args:
            tts_dir: Directory for temporary TTS files
            audio_dir: Directory for pre-cached audio files
        """
        self.tts_dir = tts_dir
        self.audio_dir = audio_dir

    async def play_precached(self, ws: WebSocket, key: str, audio_done_event: asyncio.Event):
        """
        Play pre-cached audio file.

        Args:
            ws: WebSocket connection to send play command
            key: Audio key (without .wav extension)
            audio_done_event: Event to wait for playback completion
        """
        audio_done_event.clear()
        await ws.send_json({"type": "play_audio", "key": key})
        await audio_done_event.wait()

    async def synthesize_and_play(self, ws: WebSocket, text: str, audio_done_event: asyncio.Event):
        """
        Synthesize text to TTS and play, then cleanup temp file.

        Args:
            ws: WebSocket connection to send play command
            text: Text to synthesize
            audio_done_event: Event to wait for playback completion
        """
        result = await tts.synthesize_to_temp_wav(text, self.tts_dir)
        if result is None:
            return

        key, wav_path = result
        try:
            audio_done_event.clear()
            await ws.send_json({"type": "play_audio", "key": key, "tts": True})
            await audio_done_event.wait()
        finally:
            # Always cleanup temp file
            try:
                os.unlink(wav_path)
            except OSError:
                pass

    async def play_or_say(
        self,
        ws: WebSocket,
        key: str,
        fallback_text: str,
        audio_done_event: asyncio.Event
    ):
        """
        Play pre-cached audio if available, otherwise synthesize dynamically.

        Args:
            ws: WebSocket connection
            key: Pre-cached audio key
            fallback_text: Fallback text for dynamic TTS if no pre-cache
            audio_done_event: Event to wait for playback completion
        """
        wav = os.path.join(self.audio_dir, f"{key}.wav")
        if os.path.isfile(wav):
            await self.play_precached(ws, key, audio_done_event)
        elif fallback_text:
            await self.synthesize_and_play(ws, fallback_text, audio_done_event)
        # Else: no pre-cache + no fallback -> silent (same as original)

    def get_precached_path(self, key: str) -> str:
        """
        Get full path to pre-cached audio file.

        Args:
            key: Audio key (without .wav extension)

        Returns:
            Full path to audio file
        """
        return os.path.join(self.audio_dir, f"{key}.wav")

    def has_precached(self, key: str) -> bool:
        """
        Check if pre-cached audio file exists.

        Args:
            key: Audio key (without .wav extension)

        Returns:
            True if pre-cached file exists
        """
        return os.path.isfile(self.get_precached_path(key))
