"""Game 1 (Cầu Vồng) — judge logic. Trước Phase 2: ZERO test cho Trò 1.
Test fuzzy match (alias), template fallback (llm=None), LLM stub path, + data invariants."""
from unittest.mock import MagicMock

from games.cau_vong.services.judge_service import JudgeService
from koon_data import CHALLENGES, INTRO, INTRO_LINES


def _stub_llm(content: str):
    """Mock OpenAI client trả content cố định từ chat.completions.create."""
    llm = MagicMock()
    llm.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=content))]
    )
    return llm


def test_judge_fuzzy_matches_aliases():
    ch = CHALLENGES[0]   # dưa hấu, aliases ["trái dưa hấu","qua dua ho","dua hấu","dưa"]
    assert judge_fuzzy("dưa hấu", ch) is True
    assert judge_fuzzy("qua dua ho", ch) is True       # alias không dấu
    assert judge_fuzzy("DƯA", ch) is True              # uppercase của alias "dưa" (.lower() → "dưa")
    assert judge_fuzzy("con mèo", ch) is False
    assert judge_fuzzy("", ch) is False


def test_judge_and_reply_fuzzy_match_returns_empty_reply():
    """Fuzzy khớp đáp án dự định → (True, '') → flow dùng pre-cache right (nhanh)."""
    ch = CHALLENGES[0]
    correct, reply = judge_and_reply("dưa hấu", ch, 0, llm=None)
    assert correct is True
    assert reply == ""


def test_judge_and_reply_wrong_no_llm_uses_template():
    """SAI + không LLM → reply template chứa hint, không tiết lộ đáp án."""
    ch = CHALLENGES[1]   # "cái bàn", hint về đồ vật 4 chân ngồi học
    correct, reply = judge_and_reply("con chó", ch, 0, llm=None)
    assert correct is False
    assert "bốn chân" in reply or "chân" in reply     # có gợi ý
    assert "bàn" not in reply                           # KHÔNG tiết lộ đáp án


def test_judge_and_reply_llm_correct_stub():
    """LLM stub trả correct:true → (True, reply động)."""
    ch = CHALLENGES[1]
    llm = _stub_llm('{"correct": true, "reply": "Đúng rồi! Ghế cũng có 4 chân!"}')
    correct, reply = judge_and_reply("ghế", ch, 0, llm=llm, model="stub-model")
    assert correct is True
    assert reply == "Đúng rồi! Ghế cũng có 4 chân!"
    # model truyền vào create
    assert llm.chat.completions.create.call_args.kwargs["model"] == "stub-model"


def test_judge_and_reply_llm_bad_json_falls_back_to_template():
    """LLM trả non-JSON → catch → template fallback (không crash)."""
    ch = CHALLENGES[0]
    llm = _stub_llm("Sorry, tôi không hiểu.")   # không phải JSON
    correct, reply = judge_and_reply("xyz", ch, 0, llm=llm, model="m")
    assert correct is False
    assert reply  # có reply template


def test_data_invariants():
    """INTRO (asset keys) và INTRO_LINES (fallback text) phải cùng độ dài
    (flow zip theo index — trước đây 2 list khác nguồn, dễ drift)."""
    assert len(INTRO) == len(INTRO_LINES) == 5
    assert len(CHALLENGES) == 7
    # Mỗi challenge có đủ các asset key + nội dung
    for ch in CHALLENGES:
        assert ch.q and ch.right and ch.question_text and ch.answer and ch.hint
        assert ch.color and ch.hex
