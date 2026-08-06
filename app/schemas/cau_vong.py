"""Typed domain models Trò 1 (Cầu Vồng) — thay thế dict cho CHALLENGES."""
from enum import Enum

from pydantic import BaseModel


class Game1Phase(str, Enum):
    """Các phase của flow Cầu Vồng (trước đây stringly-typed, typo fail silent)."""
    IDLE = "idle"
    INTRO = "intro"
    ASK = "ask"
    AWAIT = "await"
    FEEDBACK = "feedback"
    RAINBOW = "rainbow"
    RECAP = "recap"
    DONE = "done"


class Challenge(BaseModel):
    """1 thử thách cầu vồng. q/right/wrong là asset key (pre-cache), nội dung là câu đố."""
    n: int
    color: str
    hex: str
    q: str               # asset key câu hỏi
    right: str           # asset key phản hồi đúng
    wrong: str           # asset key phản hồi sai (dự phòng — hiện dùng LLM reply)
    question_text: str
    answer: str
    aliases: list[str] = []
    hint: str
