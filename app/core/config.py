"""Config tập trung — thay thế os.environ.get rải rác ở 4 file (server, timnang, 2 script gen).

Đọc 1 lần lúc import. Phase 3 sẽ nâng lên pydantic-settings + validation + .env loader;
Phase 1 chỉ tập trung nguồn đọc (behavior-preserving, không thêm dependency).
"""
import os

from . import constants as C


class Settings:
    """Toàn bộ env vars dự án. Truy cập qua `settings.<attr>`."""

    # OpenRouter — dùng chung cho LLM (Trò 1) + vision (Trò 2)
    openrouter_api_key: str = os.environ.get("OPENROUTER_API_KEY", "").strip()
    or_model: str = os.environ.get("OR_MODEL", C.DEFAULT_MODEL)

    # Kokoro / edge TTS — dùng chung cả 2 trò
    koon_voice: str = os.environ.get("KOON_VOICE", C.DEFAULT_VOICE)
    koon_gen_engine: str = os.environ.get("KOON_GEN_ENGINE", C.DEFAULT_GEN_ENGINE)
    koon_voice_edge: str = os.environ.get("KOON_VOICE_EDGE", C.DEFAULT_VOICE_EDGE)
    koon_rate: str = os.environ.get("KOON_RATE", C.DEFAULT_RATE)


settings = Settings()
