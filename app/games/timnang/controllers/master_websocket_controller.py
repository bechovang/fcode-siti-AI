"""
Master/operator WebSocket controller for Tìm Nắng (Game 2).
"""

import logging
from typing import Callable, Any

from fastapi import WebSocket
from core.ws import recv_json
from games.timnang.controllers.base import WebSocketController

log = logging.getLogger("timnang.master")


class MasterWebSocketController(WebSocketController):
    """WebSocket controller for master/operator connections."""

    def __init__(self, get_service: Callable[[str], Any]):
        """
        Initialize master WebSocket controller.

        Args:
            get_service: Service factory function
        """
        super().__init__(get_service)

    async def handle_connection(self, ws: WebSocket, **kwargs):
        """
        Handle master WebSocket connection.

        Args:
            ws: WebSocket connection
            **kwargs: Additional parameters (unused for master)
        """
        await ws.accept()
        log.info("Master/operator connected (total: %d)", len(kwargs.get("master_count", 0)))

        # Register master with broadcast service
        broadcast = self.get_service("broadcast_service")
        await broadcast.register_master(ws)

        # Send initial scoreboard
        object_repo = self.get_service("game_object_repository")
        await self._send_json(ws, broadcast.create_scoreboard_message(object_repo))

        try:
            await self._message_loop(ws)
        except Exception as e:
            log.error("Master WebSocket error: %s", e)
        finally:
            await self._cleanup(ws)

    async def _message_loop(self, ws: WebSocket):
        """
        Main message loop for master/operator.

        Args:
            ws: WebSocket connection
        """
        while True:
            msg = await self._recv_json(ws)
            if msg is None:
                continue

            if msg.get("type") == "op":
                await self._handle_operator_action(msg)

    async def _handle_operator_action(self, msg: dict):
        """
        Handle operator action commands.

        Args:
            msg: Message containing action details
        """
        action = msg.get("action")
        round_service = self.get_service("round_service")

        if action == "start":
            await round_service.start_game()

        elif action == "restart":
            await round_service.operator_reset_game()

        elif action == "force_accept":
            team = msg.get("team")
            if team:
                await round_service.operator_force_accept(team)

        elif action == "add_point":
            team = msg.get("team")
            delta = msg.get("delta", 1)
            if team:
                await round_service.operator_add_point(team, delta)

        elif action == "skip_round":
            await round_service.operator_skip_round()

        elif action == "next_round":
            game_state = self.get_service("game_state_service")
            object_repo = self.get_service("game_object_repository")
            current_round = game_state.get_round_index()
            next_round = current_round + 1

            if next_round < object_repo.count():
                await round_service.start_round(next_round)
            else:
                # Skip to game over
                await round_service.operator_skip_round()  # This will trigger game over

    async def _cleanup(self, ws: WebSocket):
        """
        Cleanup when master disconnects.

        Args:
            ws: WebSocket connection
        """
        broadcast = self.get_service("broadcast_service")
        await broadcast.unregister_master(ws)
        log.info("Master disconnected")
