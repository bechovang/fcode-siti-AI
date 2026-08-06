"""Integration Trò 2 — vision judge + recognize round-trip.
Migrated từ app/scripts/_tn_test.py (script manual, không assertion, cần server running).
Bản này: vision MOCK (không cần API key/server), assertion thật, chạy trong pytest."""
from unittest.mock import MagicMock

from games.timnang.services.vision_service import VisionService
from games.timnang.services.game_state_service import GameStateService
from games.timnang.services.round_service import RoundService
from games.timnang.repositories.game_object_repository import GameObjectRepository
from games.timnang.repositories.team_repository import TeamRepository
from timnang_data import TEAMS, SCORE_BY_ORDER, ORDER_WORD, _NUM_VI, num_vi
from schemas.timnang import TeamState


def _stub_llm(content: str):
    """Mock OpenAI client trả content cố định."""
    llm = MagicMock()
    llm.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=content))]
    )
    return llm


async def test_judge_vision_true_false_none():
    """Vision judge: stub trả correct:true/false → bool; llm=None → None (operator duyệt tay)."""
    obj = OBJECTS[0]
    assert await judge_vision("data:image/jpeg;base64,xxx", obj, _stub_llm('{"correct": true}'), "m") is True
    assert await judge_vision("data:image/jpeg;base64,xxx", obj, _stub_llm('{"correct": false}'), "m") is False
    assert await judge_vision("data:image/jpeg;base64,xxx", obj, None, "m") is None


async def test_handle_recognize_correct_assigns_order(monkeypatch):
    """Full chain recognize → vision(correct) → _assign_order. Vision mock True."""
    g = Game()
    g.phase = "playing"
    g.object = OBJECTS[0]

    async def _vision_true(img, obj, llm, model):
        return True

    monkeypatch.setattr("games.timnang.game.judge_vision", _vision_true)
    await g.handle_recognize("A", "data:image/jpeg;base64,xxx")
    assert g.teams["A"]["order"] == 1
    assert g.teams["A"]["score"] == 3


async def test_handle_recognize_wrong_no_assign(monkeypatch):
    """Vision False → không gán order, score giữ 0."""
    g = Game()
    g.phase = "playing"
    g.object = OBJECTS[0]

    async def _vision_false(img, obj, llm, model):
        return False

    monkeypatch.setattr("games.timnang.game.judge_vision", _vision_false)
    await g.handle_recognize("A", "data:image/jpeg;base64,xxx")
    assert g.teams["A"]["order"] is None
    assert g.teams["A"]["score"] == 0


async def test_handle_recognize_vision_none_no_assign(monkeypatch):
    """Vision None (AI không chắc) → không assign, chờ operator force_accept."""
    g = Game()
    g.phase = "playing"
    g.object = OBJECTS[0]

    async def _vision_none(img, obj, llm, model):
        return None

    monkeypatch.setattr("games.timnang.game.judge_vision", _vision_none)
    await g.handle_recognize("A", "data:image/jpeg;base64,xxx")
    assert g.teams["A"]["order"] is None
