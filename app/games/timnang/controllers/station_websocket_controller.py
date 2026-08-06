"""
Station WebSocket controller for Tìm Nắng (Game 2).
"""

import logging
from typing import Callable, Any

from fastapi import WebSocket
from core.ws import recv_json
from games.timnang.controllers.base import WebSocketController

log = logging.getLogger("timnang.station")


class StationWebSocketController(WebSocketController):
    """WebSocket controller for station connections."""

    def __init__(self, get_service: Callable[[str], Any]):
        """
        Initialize station WebSocket controller.

        Args:
            get_service: Service factory function
        """
        super().__init__(get_service)

    async def handle_connection(self, ws: WebSocket, **kwargs):
        """
        Handle station WebSocket connection.

        Args:
            ws: WebSocket connection
            **kwargs: Must contain 'team' parameter
        """
        team = kwargs.get("team")
        if not team:
            await ws.close(code=1008, reason="No team specified")
            return

        # Validate team exists
        team_repo = self.get_service("team_repository")
        if not team_repo.team_exists(team):
            await ws.close(code=1008, reason=f"Unknown team: {team}")
            return

        await ws.accept()
        log.info("Station [%s] connected", team)

        # Register station with broadcast service
        broadcast = self.get_service("broadcast_service")
        await broadcast.register_station(team, ws)

        # Send initial scoreboard
        object_repo = self.get_service("game_object_repository")
        await self._send_json(ws, broadcast.create_scoreboard_message(object_repo))

        # Send current round info if game in progress
        game_state = self.get_service("game_state_service")
        current_object_id = game_state.get_current_object_id()
        if current_object_id:
            obj = object_repo.get_by_id(current_object_id)
            if obj:
                await self._send_json(ws, {
                    "type": "round",
                    "object": obj.name,
                    "vi": obj.vi
                })

        try:
            await self._message_loop(ws, team)
        except Exception as e:
            log.error("Station [%s] WebSocket error: %s", team, e)
        finally:
            await self._cleanup(team, ws)

    async def _message_loop(self, ws: WebSocket, team: str):
        """
        Main message loop for station.

        Args:
            ws: WebSocket connection
            team: Team ID
        """
        while True:
            msg = await self._recv_json(ws)
            if msg is None:
                continue

            if msg.get("type") == "recognize":
                await self._handle_recognize(team, msg)

    async def _handle_recognize(self, team: str, msg: dict):
        """
        Handle recognition request from station.

        Args:
            team: Team ID
            msg: Message containing image data
        """
        image_b64 = msg.get("image", "")

        if not image_b64:
            await self._send_json_error(msg_type="result", correct=False, msg="Camera chưa sẵn sàng — thử lại nhé!")
            return

        # Get round service to handle recognition
        round_service = self.get_service("round_service")
        vision_service = self.get_service("vision_service")

        result = await round_service.handle_recognition(team, image_b64, vision_service)

        if result:
            await self._send_json(result)

    async def _send_json_error(self, msg_type: str, correct: bool, msg: str):
        """Send error result message."""
        await self._send_json(None, {"type": msg_type, "correct": correct, "msg": msg})  # ws will be set by base class

    async def _cleanup(self, team: str, ws: WebSocket):
        """
        Cleanup when station disconnects.

        Args:
            team: Team ID
            ws: WebSocket connection
        """
        broadcast = self.get_service("broadcast_service")
        await broadcast.unregister_station(team, ws)
        log.info("Station [%s] disconnected", team)
