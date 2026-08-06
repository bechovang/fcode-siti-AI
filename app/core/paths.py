"""Đường dẫn app — thay thế APP_DIR/STATIC_DIR/TTS_DIR boilerplate duplicate giữa 2 server."""
import os
import tempfile

# app/core/paths.py → app/
APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(APP_DIR, "static")
ASSETS_DIR = os.path.join(APP_DIR, "assets")
AUDIO_BASE = os.path.join(ASSETS_DIR, "audio")        # chứa koon/ + timnang/ (pre-cache)
VIDEO_DIR = os.path.join(ASSETS_DIR, "video")         # recap mp4 (Trò 1)
# Live2D model từ ref/ (gitignored — fallback emoji 🦊 nếu thiếu)
LIVE2D_DIR = os.path.normpath(os.path.join(APP_DIR, "..", "ref", "Open-LLM-VTuber", "live2d-models"))


def audio_dir(game: str) -> str:
    """Thư mục pre-cache giọng của 1 game: app/assets/audio/<game>."""
    return os.path.join(AUDIO_BASE, game)


def new_tts_dir(prefix: str = "tts_") -> str:
    """Temp dir cho WAV sinh động (mỗi server tạo 1 dir riêng lúc boot)."""
    return tempfile.mkdtemp(prefix=prefix)
