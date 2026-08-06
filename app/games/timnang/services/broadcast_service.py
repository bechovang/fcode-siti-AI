"""
Service for WebSocket broadcasting to masters and stations.
"""

import asyncio
import logging
from typing import Dict, Set, Optional
from fastapi import WebSocket

from core.ws import safe_send
from games.timnang.services.game_state_service import GameStateService
from games.timnang.repositories.team_repository import TeamRepository

log = logging.getLogger("timnang.broadcast")


class BroadcastService:
    """Service for broadcasting messages to masters and stations."""

    def __init__(
        self,
        game_state: GameStateService,
        team_repo: TeamRepository,
    ):
        """
        Initialize broadcast service.

        Args:
            game_state: Game state service
            team_repo: Team repository for validation
        """
        self.game_state = game_state
        self.team_repo = team_repo

        self.stations: Dict[str, WebSocket] = {}  # team_id -> ws
        self.masters: Set[WebSocket] = set()

    async def register_master(self, ws: WebSocket):
        """Register master WebSocket connection."""
        self.masters.add(ws)
        log.info("Master connected (total: %d)", len(self.masters))

    async def unregister_master(self, ws: WebSocket):
        """Unregister master WebSocket connection."""
        self.masters.discard(ws)
        log.info("Master disconnected (total: %d)", len(self.masters))

    async def register_station(self, team_id: str, ws: WebSocket) -> bool:
        """
        Register station WebSocket connection.

        Args:
            team_id: Team ID
            ws: WebSocket connection

        Returns:
            True if registered successfully, False if team invalid
        """
        if not self.team_repo.team_exists(team_id):
            return False

        self.stations[team_id] = ws
        log.info("Station %s registered (total: %d)", team_id, len(self.stations))
        return True

    async def unregister_station(self, team_id: str, ws: WebSocket):
        """Unregister station WebSocket connection."""
        if self.stations.get(team_id) is ws:
            del self.stations[team_id]
            log.info("Station %s unregistered (total: %d)", team_id, len(self.stations))

    async def send_to_master(self, ws: WebSocket, msg: dict):
        """Send message to specific master."""
        await safe_send(ws, msg)

    async def send_to_station(self, team_id: str, msg: dict):
        """Send message to specific station."""
        ws = self.stations.get(team_id)
        if ws:
            await safe_send(ws, msg)

    async def broadcast_masters(self, msg: dict):
        """Broadcast message to all masters."""
        for ws in list(self.masters):
            await safe_send(ws, msg)

    async def broadcast_stations(self, msg: dict):
        """Broadcast message to all stations."""
        for ws in list(self.stations.values()):
            await safe_send(ws, msg)

    async def broadcast_all(self, msg: dict):
        """Broadcast message to both masters and stations."""
        await self.broadcast_masters(msg)
        await self.broadcast_stations(msg)

    def create_scoreboard_message(self, object_repo) -> dict:
        """Create scoreboard message for current state."""
        teams = self.game_state.get_all_teams()
        current_object_id = self.game_state.get_current_object_id()

        # Get current object name if in playing phase
        obj_name = None
        obj_vi = None
        if current_object_id and self.game_state.get_phase().name == "PLAYING":
            obj = object_repo.get_by_id(current_object_id)
            if obj:
                obj_name = obj.name
                obj_vi = obj.vi

        return {
            "type": "scoreboard",
            "phase": self.game_state.get_phase(),
            "round": self.game_state.get_round_index() + 1 if self.game_state.get_round_index() >= 0 else 0,
            "rounds": self.game_state.get_round_index() + 6,  # Will be corrected by caller
            "object": obj_name,
            "object_vi": obj_vi,
            "teams": [
                {
                    "id": tid,
                    "name": t["name"],
                    "color": t["color"],
                    "score": t["score"],
                    "order": t["order"]
                }
                for tid, t in teams.items()
            ],
        }

    async def sync_scoreboard(self, object_repo):
        """Broadcast current scoreboard state."""
        msg = self.create_scoreboard_message(object_repo)
        await self.broadcast_all(msg)

    def get_station_count(self) -> int:
        """Get number of connected stations."""
        return len(self.stations)

    def get_master_count(self) -> int:
        """Get number of connected masters."""
        return len(self.masters)

    def is_station_connected(self, team_id: str) -> bool:
        """Check if specific station is connected."""
        return team_id in self.stations
