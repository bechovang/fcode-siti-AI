"""Audio route — thay thế /audio/{key} duplicate + path traversal fix (Phase 0).

Cả 2 server có cùng fallback chain: temp TTS wav → pre-cache wav → pre-cache mp3 → 404.
`register_audio_route` gắn GET /audio/{key} lên app; `resolve_audio_path` expose để test.
"""
import os

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse


def safe_audio_key(key: str) -> str:
    """Chuẩn hoá key audio về basename (bỏ đuôi .wav/.mp3).
    Chặn path traversal: key là trust boundary từ URL — không cho '..' '/' '\\' thoát thư mục."""
    base = os.path.basename(key.replace("\\", "/"))
    return base.replace(".wav", "").replace(".mp3", "")


def resolve_audio_path(key: str, tts_dir: str, audio_dir: str) -> tuple[str, str] | None:
    """Trả (path, media_type) hoặc None. Thứ tự: temp TTS wav → pre-cache wav → pre-cache mp3."""
    extless = safe_audio_key(key)
    tts_wav = os.path.join(tts_dir, f"{extless}.wav")
    if os.path.isfile(tts_wav):
        return tts_wav, "audio/wav"
    pc_wav = os.path.join(audio_dir, f"{extless}.wav")
    if os.path.isfile(pc_wav):
        return pc_wav, "audio/wav"
    pc_mp3 = os.path.join(audio_dir, f"{extless}.mp3")
    if os.path.isfile(pc_mp3):
        return pc_mp3, "audio/mpeg"
    return None


def register_audio_route(app: FastAPI, tts_dir: str, audio_dir: str) -> None:
    """Gắn GET /audio/{key} lên app với fallback chain + sanitize path traversal."""

    @app.get("/audio/{key}")
    async def audio(key: str):
        resolved = resolve_audio_path(key, tts_dir, audio_dir)
        if resolved:
            path, media_type = resolved
            return FileResponse(path, media_type=media_type)
        return JSONResponse({"error": "not found", "key": key}, status_code=404)
