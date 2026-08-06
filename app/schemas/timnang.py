"""Typed domain models Trò 2 (Tìm Nắng) — thay thế dict cho OBJECTS/TEAMS."""
from enum import Enum
from typing import TypedDict

from pydantic import BaseModel


class Game2Phase(str, Enum):
    """Các phase của Game state machine (trước đây stringly-typed)."""
    IDLE = "idle"
    ANNOUNCE = "announce"
    PLAYING = "playing"
    ROUND_END = "round_end"
    GAME_OVER = "game_over"


class GameObject(BaseModel):
    """1 vật phẩm cần tìm trong 1 vòng."""
    id: str
    name: str
    vi: str
    aliases: list[str] = []
    vision_prompt: str        # mô tả tiếng Anh cho GPT-4o-mini vision


class Team(BaseModel):
    """1 đội đối kháng."""
    id: str
    name: str
    color: str


class TeamState(TypedDict):
    """Runtime state của 1 đội trong 1 Game (mutable — dict value trong Game.teams)."""
    name: str
    color: str
    score: int
    order: int | None
    last_rec: float
