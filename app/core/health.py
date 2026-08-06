"""Health payload — thay thế /health skeleton duplicate.

2 game có shape /health khác nhau (Trò 1: tts_model/stt/live2d; Trò 2: game/vision/teams/...),
nhưng chung khối ok/tts/tts_voice. `base_health` cung cấp khối chung đọc từ settings;
mỗi game merge thêm trường riêng — giữ shape JSON của mỗi game nguyên vẹn.
"""
from .config import settings


def base_health(*, tts_ok: bool) -> dict:
    """Khối chung cho /health. Mỗi game merge thêm trường riêng vào dict này."""
    return {
        "ok": True,
        "tts": tts_ok,
        "tts_voice": settings.koon_voice,
    }
