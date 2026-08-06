"""
Service for session lifecycle and state management.
"""

import asyncio
import json
import logging
from typing import Optional

from core.ws import safe_send
from schemas.cau_vong import Game1Phase
from games.cau_vong.models import SessionState
from games.cau_vong.services.tts_service import TTSService

log = logging.getLogger("koon.session")


class SessionManager:
    """Service for managing game session state and communication."""

    def __init__(self, ws: "WebSocket", tts_service: TTSService):
        """
        Initialize session manager.

        Args:
            ws: WebSocket connection
            tts_service: TTS service for audio playback
        """
        self.ws = ws
        self.tts_service = tts_service
        self.state = SessionState()

        # Async events for coordination
        self._audio_done = asyncio.Event()
        self._answer_ready = asyncio.Event()
        self._video_done = asyncio.Event()

        # Operator control
        self._op: Optional[str] = None  # skip | force_correct | replay

        # User's answer
        self._answer: Optional[str] = None

    async def send_message(self, msg: dict):
        """
        Send message through WebSocket (raises on error - intentional for flow recovery).

        Args:
            msg: Message dictionary to send
        """
        await self.ws.send_text(json.dumps(msg, ensure_ascii=False))

    async def send_state(self, total_challenges: int):
        """
        Send current state to client.

        Args:
            total_challenges: Total number of challenges (always 7)
        """
        await self.send_message({
            "type": "state",
            "phase": self.state.phase,
            "idx": self.state.challenge_index,
            "unlocked": self.state.unlocked_colors,
            "total": total_challenges,
        })

    async def play_audio(self, key: str):
        """
        Play pre-cached audio.

        Args:
            key: Audio key (without .wav extension)
        """
        await self.tts_service.play_precached(self.ws, key, self._audio_done)

    async def say_text(self, text: str):
        """
        Synthesize and play TTS text.

        Args:
            text: Text to synthesize
        """
        await self.tts_service.synthesize_and_play(self.ws, text, self._audio_done)

    async def play_or_say(self, key: str, fallback_text: str = ""):
        """
        Play pre-cached if available, otherwise synthesize dynamically.

        Args:
            key: Pre-cached audio key
            fallback_text: Fallback text for dynamic TTS
        """
        await self.tts_service.play_or_say(self.ws, key, fallback_text, self._audio_done)

    def interrupt(self):
        """Interrupt all blocking waits for operator control."""
        self._audio_done.set()
        self._answer_ready.set()
        self._video_done.set()

    def reset(self):
        """Reset session to initial state."""
        self.state.reset()
        self._op = None
        self._answer = None
        # Clear events
        self._audio_done.clear()
        self._answer_ready.clear()
        self._video_done.clear()

    # Answer handling
    def set_answer(self, answer: str):
        """Set user's answer and signal ready."""
        self._answer = answer
        self._answer_ready.set()

    async def wait_for_answer(self):
        """Wait for user's answer (can be interrupted)."""
        self._answer_ready.clear()
        self._answer = None
        self._answer_ready.wait()

    def get_answer(self) -> str:
        """Get user's answer."""
        return self._answer or ""

    # Video handling
    async def wait_for_video_end(self):
        """Wait for video playback to end (can be interrupted)."""
        self._video_done.clear()
        self._video_done.wait()

    # Operator controls
    def set_operator_command(self, command: str):
        """Set operator command (skip/force_correct/replay)."""
        self._op = command

    def get_and_clear_operator_command(self) -> Optional[str]:
        """Get and clear operator command."""
        op = self._op
        self._op = None
        return op

    def has_operator_command(self) -> bool:
        """Check if operator command is pending."""
        return self._op is not None

    # Event getters for external coordination
    @property
    def audio_done_event(self) -> asyncio.Event:
        """Get audio completion event."""
        return self._audio_done

    @property
    def answer_ready_event(self) -> asyncio.Event:
        """Get answer ready event."""
        return self._answer_ready

    @property
    def video_done_event(self) -> asyncio.Event:
        """Get video completion event."""
        return self._video_done
