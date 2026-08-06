"""
Base WebSocket controller with common protocol handling.
"""

from fastapi import WebSocket
from typing import Callable, Dict, Any
from core.ws import recv_json, safe_send


class WebSocketController:
    """Base controller for WebSocket connections."""

    def __init__(self, get_service: Callable[[str], Any]):
        """
        Initialize controller with service factory.

        Args:
            get_service: Function that returns service instances by name
        """
        self.get_service = get_service

    async def handle_connection(self, ws: WebSocket, **kwargs):
        """
        Handle WebSocket connection lifecycle.

        Args:
            ws: WebSocket connection
            **kwargs: Additional parameters from route (e.g., team name)
        """
        await ws.accept()
        try:
            await self._message_loop(ws, **kwargs)
        except Exception as e:
            # Log error but don't crash - close connection gracefully
            print(f"WebSocket error: {e}")
        finally:
            await self._cleanup(ws, **kwargs)

    async def _message_loop(self, ws: WebSocket, **kwargs):
        """
        Main message loop - override in subclass.

        Args:
            ws: WebSocket connection
            **kwargs: Additional parameters from route
        """
        raise NotImplementedError("Subclasses must implement _message_loop")

    async def _cleanup(self, ws: WebSocket, **kwargs):
        """
        Cleanup when connection closes - override in subclass if needed.

        Args:
            ws: WebSocket connection
            **kwargs: Additional parameters from route
        """
        pass  # Default: no cleanup needed

    async def _send_json(self, ws: WebSocket, msg: Dict[str, Any]):
        """
        Send JSON message through WebSocket.

        Args:
            ws: WebSocket connection
            msg: Message dictionary to send
        """
        await safe_send(ws, msg)

    async def _recv_json(self, ws: WebSocket) -> Dict[str, Any]:
        """
        Receive and parse JSON message from WebSocket.

        Args:
            ws: WebSocket connection

        Returns:
            Parsed message dictionary
        """
        return await recv_json(ws)
