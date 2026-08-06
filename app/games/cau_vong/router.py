"""HTTP + WS routes Trò 1 - MVC version.

register_routes(app, ...) receives controllers via dependency injection from app.py
and only handles route registration (delegates to controllers).
"""
import os
import logging

from core import paths
from core.health import base_health
from core.tts import tts_available
from fastapi.responses import FileResponse

from .controllers import CauVongWebSocketController, HealthController

log = logging.getLogger("koon.router")


def register_routes(
    app,
    *,
    websocket_controller: CauVongWebSocketController,
    health_controller: HealthController
) -> None:
    """Register all HTTP and WebSocket routes using controllers.

    Args:
        app: FastAPI application instance
        websocket_controller: WebSocket controller for game connections
        health_controller: Health controller for health endpoint
    """

    @app.websocket("/ws")
    async def ws_endpoint(websocket):
        """WebSocket endpoint - delegates to controller."""
        await websocket_controller.handle_connection(websocket)

    @app.get("/")
    async def index():
        """Serve main game page."""
        return FileResponse(os.path.join(paths.STATIC_DIR, "index.html"))

    @app.get("/health")
    async def health():
        """Health check endpoint - delegates to controller."""
        return await health_controller.get_health()
