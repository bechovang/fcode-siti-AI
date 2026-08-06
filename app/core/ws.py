"""WS helpers — thay thế send helper drift + json guard duplicate.

- `safe_send`: Trò 1 Session.send từng không guard (crash khi socket nửa đóng),
  Trò 2 Game._send swallow-all. Giờ 1 chính sách: log + không raise.
- `recv_json`: json guard ở 3 WS loop (server.py /ws, timnang /ws/station, /ws/master)
  — frame lỗi/non-dict trả None để loop `continue`, không crash connection.
"""
import json
import logging

from fastapi import WebSocket

log = logging.getLogger("core.ws")


async def safe_send(ws: WebSocket, msg: dict) -> bool:
    """Gửi WS message, không bao giờ raise. Trả True nếu gửi được."""
    try:
        await ws.send_text(json.dumps(msg, ensure_ascii=False))
        return True
    except Exception as e:
        log.debug("WS send lỗi: %s", e)
        return False


async def recv_json(ws: WebSocket) -> dict | None:
    """Nhận 1 frame → parse JSON. Trả dict, hoặc None nếu frame lỗi / non-dict (đã log).

    KHÔNG bắt WebSocketDisconnect — để nó truyền lên `except WebSocketDisconnect` của loop.
    """
    try:
        msg = json.loads(await ws.receive_text())
    except json.JSONDecodeError:
        log.warning("WS frame không hợp lệ, bỏ qua")
        return None
    if not isinstance(msg, dict):
        return None
    return msg
