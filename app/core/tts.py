"""Kokoro TTS provider — thay thế `_tts` global + `get_tts()` duplicate + flag drift
(server.py:43-65 == timnang_master.py:46-69, flag từng drift thành `TTS_AVAILABLE` vs `_TTS_OK`).

Lazy singleton, 1 availability flag duy nhất. `synthesize_to_temp_wav()` là helper chung
cho say() của cả 2 trò — thống nhất chính sách guard + timeout + sample rate (trước đây
say() của Trò 1 không guard, Trò 2 guard — drift đã fix Phase 0, giờ share code).
"""
import asyncio
import logging
import os
import uuid

from . import constants as C
from .config import settings

log = logging.getLogger("core.tts")

# 1 availability flag duy nhất (trước đây 2 tên: TTS_AVAILABLE / _TTS_OK)
_KOKORO_AVAILABLE = False
try:
    from kokoro_vietnamese import KokoroVietnamese as _KokoroTTS
    _KOKORO_AVAILABLE = True
except ImportError:
    pass


def tts_available() -> bool:
    """Kokoro đã cài chưa (không load model)."""
    return _KOKORO_AVAILABLE


_instance = None


def get_tts():
    """Trả instance Kokoro (lazy load 1 lần) hoặc None nếu chưa cài."""
    global _instance
    if not _KOKORO_AVAILABLE:
        return None
    if _instance is None:
        _instance = _KokoroTTS(device="cpu", voice=settings.koon_voice)
        log.info("Kokoro TTS sẵn sàng (giọng %s, device=cpu)", settings.koon_voice)
    return _instance


def warmup() -> None:
    """Load model ngay lúc boot (tránh lazy-init block lần say() đầu). Gọi từ entry point."""
    get_tts()


async def synthesize_to_temp_wav(text: str, tts_dir: str) -> tuple[str, str] | None:
    """Synthesize Kokoro → ghi WAV vào tts_dir. Trả (key, path) hoặc None nếu TTS lỗi/chưa cài.

    Chính sách thống nhất: try/except + timeout (TTS_TIMEOUT) — KHÔNG bao giờ raise
    (caller — run_flow / end_round — không bị crash/kẹt khi TTS lỗi/chậm).
    """
    import soundfile as sf  # import lười để core import được kể cả khi thiếu soundfile
    tts = get_tts()
    if tts is None:
        log.warning("TTS không có — bỏ qua: '%s'", text[:50])
        return None
    try:
        audio, _phonemes = await asyncio.wait_for(
            asyncio.to_thread(tts.synthesize, text), timeout=C.TTS_TIMEOUT)
        key = f"tts_{uuid.uuid4().hex}"
        wav_path = os.path.join(tts_dir, f"{key}.wav")
        sf.write(wav_path, audio, C.TTS_SAMPLE_RATE)
        log.debug("TTS [%s] '%s'", key, text[:50])
        return key, wav_path
    except asyncio.TimeoutError:
        log.warning("[TTS timeout] synthesize quá %ds, bỏ qua: '%s'", C.TTS_TIMEOUT, text[:50])
    except Exception as e:
        log.warning("[TTS lỗi] %s — bỏ qua: '%s'", e, text[:50])
    return None
