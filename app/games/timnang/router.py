"""HTTP + WS routes Trò 2 - MVC version.

register_routes(app, ...) receives controllers via dependency injection from app.py
and only handles route registration (delegates to controllers).
"""
import os
import logging

from core import paths
from core.health import base_health
from core.tts import tts_available
from fastapi.responses import FileResponse, JSONResponse
from fastapi import WebSocket

from games.timnang.controllers import StationWebSocketController, MasterWebSocketController, HealthController
from games.timnang.repositories.team_repository import TeamRepository

log = logging.getLogger("timnang.router")


def register_routes(
    app,
    *,
    station_controller: StationWebSocketController,
    master_controller: MasterWebSocketController,
    health_controller: HealthController,
    team_repo: TeamRepository
) -> None:
    """Register all HTTP and WebSocket routes using controllers.

    Args:
        app: FastAPI application instance
        station_controller: Station WebSocket controller
        master_controller: Master WebSocket controller
        health_controller: Health controller for health endpoint
        team_repo: Team repository for validation
    """

    @app.get("/")
    async def master_page():
        """Serve master/operator page."""
        return FileResponse(os.path.join(paths.STATIC_DIR, "timnang", "master.html"))

    @app.get("/station/{team}")
    async def station_page(team: str):
        """Serve station page with team validation."""
        if not team_repo.team_exists(team):
            return JSONResponse({"error": "team unknown", "team": team}, status_code=404)
        return FileResponse(os.path.join(paths.STATIC_DIR, "timnang", "station.html"))

    @app.get("/health")
    async def health():
        """Health check endpoint - delegates to controller."""
        return await health_controller.get_health()

    # ---------- WebSocket: station ----------
    @app.websocket("/ws/station/{team}")
    async def ws_station(websocket: WebSocket, team: str):
        """Station WebSocket endpoint - delegates to controller."""
        await station_controller.handle_connection(websocket, team=team)

    # ---------- WebSocket: master/operator ----------
    @app.websocket("/ws/master")
    async def ws_master(websocket: WebSocket):
        """Master/operator WebSocket endpoint - delegates to controller."""
        await master_controller.handle_connection(websocket)
