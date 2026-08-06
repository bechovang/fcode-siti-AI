"""
WebSocket controller for Cầu Vồng (Game 1).
"""

import asyncio
import logging
from typing import Callable, Any, Optional

from fastapi import WebSocket
from core.ws import recv_json
from games.cau_vong.controllers.base import WebSocketController
from games.cau_vong.services.session_manager import SessionManager
from games.cau_vong.services.game_flow_service import GameFlowService

log = logging.getLogger("koon.router")


class CauVongWebSocketController(WebSocketController):
    """WebSocket controller for Game 1 connections."""

    def __init__(
        self,
        get_service: Callable[[str], Any],
        session_manager_factory: Callable,
        game_flow_factory: Callable
    ):
        """
        Initialize WebSocket controller.

        Args:
            get_service: Service factory function
            session_manager_factory: Factory to create SessionManager instances
            game_flow_factory: Factory to create GameFlowService instances
        """
        super().__init__(get_service)
        self.session_manager_factory = session_manager_factory
        self.game_flow_factory = game_flow_factory

    async def handle_connection(self, ws: WebSocket, **kwargs):
        """
        Handle WebSocket connection lifecycle.

        Args:
            ws: WebSocket connection
            **kwargs: Additional parameters (unused for Game 1)
        """
        await ws.accept()

        # Create session and game flow instances
        session = self.session_manager_factory(ws=ws)
        game_flow = self.game_flow_factory(session_manager=session)

        await self._send_ready(ws)

        try:
            await self._message_loop(ws, session, game_flow)
        except Exception as e:
            log.error("WebSocket error: %s", e)
        finally:
            await self._cleanup(session)

    async def _send_ready(self, ws: WebSocket):
        """Send ready message to client."""
        await self._send_json(ws, {"type": "ready"})

    async def _message_loop(
        self,
        ws: WebSocket,
        session: SessionManager,
        game_flow: GameFlowService
    ):
        """
        Main message loop.

        Args:
            ws: WebSocket connection
            session: Session manager instance
            game_flow: Game flow service instance
        """
        flow_task: Optional[asyncio.Task] = None

        async def start_game():
            """Start or restart game flow."""
            if flow_task and not flow_task.done():
                flow_task.cancel()
            session.reset()
            await session.send_message({"type": "reset"})
            return asyncio.create_task(game_flow.run_full_game())

        try:
            while True:
                msg = await self._recv_json(ws)
                if msg is None:
                    continue

                msg_type = msg.get("type")

                if msg_type == "start":
                    flow_task = await start_game()

                elif msg_type == "audio_ended":
                    session.audio_done_event.set()

                elif msg_type in ("video_ended", "overlay_ended"):
                    session.video_done_event.set()

                elif msg_type == "answer":
                    answer_text = msg.get("text", "")
                    stt_source = msg.get("stt") or "typed"
                    log.info("Answer [%s]: '%s'", stt_source, answer_text)
                    session.set_answer(answer_text)
                    session.answer_ready_event.set()

                elif msg_type == "op":
                    await self._handle_operator_action(
                        msg.get("action"),
                        session,
                        start_game
                    )

        except Exception as e:
            log.exception("Message loop error: %s", e)
            raise

    async def _handle_operator_action(
        self,
        action: str,
        session: SessionManager,
        start_game: Callable
    ):
        """
        Handle operator control actions.

        Args:
            action: Operator action name
            session: Session manager instance
            start_game: Function to start/restart game
        """
        if action == "restart":
            await start_game()

        elif action == "force_correct":
            session.set_operator_command("force_correct")
            session.interrupt()

        elif action == "skip":
            session.set_operator_command("skip")
            await session.send_message({"type": "stop_audio"})
            session.interrupt()

        elif action == "replay":
            session.set_operator_command("replay")
            await session.send_message({"type": "stop_audio"})
            session.interrupt()

    async def _cleanup(self, session: SessionManager):
        """
        Cleanup when connection closes.

        Args:
            session: Session manager instance
        """
        # Cancel any running flow task
        if hasattr(session, 'flow_task'):
            flow_task = getattr(session, 'flow_task')
            if flow_task and not flow_task.done():
                flow_task.cancel()
