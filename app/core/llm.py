"""OpenRouter client — thay thế init block duplicate (server.py:37-40 == timnang_master.py:40-43).

Một chỗ duy nhất để thêm retry/backoff sau này. Trả None nếu chưa set key (chế độ dự phòng).
"""

from openai import OpenAI

from . import constants as C
from .config import settings


def make_openrouter_client() -> OpenAI | None:
    """OpenAI-compatible client trỏ sang OpenRouter, hoặc None nếu thiếu key."""
    if not settings.openrouter_api_key:
        return None
    return OpenAI(base_url=C.OR_BASE, api_key=settings.openrouter_api_key)
