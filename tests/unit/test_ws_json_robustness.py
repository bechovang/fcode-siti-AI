"""Regression: json.loads không guard ở WS receive loop (cả 3 endpoint).
Trước fix: 1 frame non-JSON → JSONDecodeError crash cả receive loop →
station/master/operator bị disconnect giữa vòng (1 message hỏng = gãy cả kết nối).
Sau fix: frame lỗi được log + bỏ qua (continue), loop sống tiếp."""
import server
import timnang_master as tm
from fastapi.testclient import TestClient


def test_game1_ws_survives_bad_json():
    """Trò 1 /ws: sau frame lỗi, op 'skip' vẫn gửi 'stop_audio' → loop còn sống."""
    client = TestClient(server.app)
    with client.websocket_connect("/ws") as ws:
        assert ws.receive_json()["type"] == "ready"
        ws.send_text("not valid json {{{")               # OLD: crash loop tại đây
        ws.send_json({"type": "op", "action": "skip"})   # skip → gửi stop_audio đồng bộ
        assert ws.receive_json()["type"] == "stop_audio"


def test_station_ws_survives_bad_json():
    """Trò 2 /ws/station/A: sau frame lỗi, recognize vẫn trả result → loop còn sống."""
    client = TestClient(tm.app)
    with client.websocket_connect("/ws/station/A") as ws:
        assert ws.receive_json()["type"] == "scoreboard"   # server gửi lúc connect
        ws.send_text("not valid json {{{")
        ws.send_json({"type": "recognize", "image": "data:image/jpeg;base64,xxx"})
        msg = ws.receive_json()
        assert msg["type"] == "result"
        assert msg["correct"] is False


def test_master_ws_survives_bad_json():
    """Trò 2 /ws/master: sau frame lỗi, op 'restart' vẫn reset (gửi stop_audio) → loop còn sống."""
    client = TestClient(tm.app)
    with client.websocket_connect("/ws/master") as ws:
        assert ws.receive_json()["type"] == "scoreboard"
        ws.send_text("not valid json {{{")
        ws.send_json({"type": "op", "action": "restart"})
        assert ws.receive_json()["type"] == "stop_audio"
