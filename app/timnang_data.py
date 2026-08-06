"""Dữ liệu Trò 2 — Tìm Nắng Cùng AI (đối kháng 3 đội, nhận diện đồ vật).
Nguồn sự thật cho master + stations + gen pre-cache TTS.

Phase 2: OBJECTS/TEAMS giờ là Pydantic GameObject/Team (typed). Logic text builder
dùng attribute access. Phase 0 fix: số→chữ (num_vi) để Kokoro đọc rõ.
"""
import os

from schemas.timnang import GameObject, Team

APP_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(APP_DIR, "static", "timnang")
AUDIO_DIR = os.path.join(APP_DIR, "assets", "audio", "timnang")  # pre-cache TTS (gitignored)

# 6 vật phẩm cần tìm. aliases không dùng cho vision (vision chấm ảnh) — giữ để
# tham khảo/hiển thị. vision_prompt = mô tả tiếng Anh cho GPT-4o-mini.
OBJECTS: list[GameObject] = [
    GameObject(id="ball",  name="quả bóng tennis", vi="quả bóng tennis",
               aliases=["bóng tennis", "quả bóng", "tennis"],
               vision_prompt="a tennis ball (small, yellow-green, fuzzy)"),
    GameObject(id="lavie", name="chai nước Lavie", vi="chai nước Lavie",
               aliases=["lavie", "nước lavie", "chai nước"],
               vision_prompt="a plastic bottle of Lavie mineral water (clear bottle, blue label, Vietnamese brand)"),
    GameObject(id="coke",  name="chai Coca-Cola", vi="chai Coca-Cola",
               aliases=["coca", "coca-cola", "coke"],
               vision_prompt="a Coca-Cola bottle or can (red label, Coca-Cola brand)"),
    GameObject(id="spoon", name="cái muỗng", vi="cái muỗng",
               aliases=["muỗng", "thìa", "spoon"],
               vision_prompt="a spoon (eating utensil)"),
    GameObject(id="tote",  name="túi Tote", vi="túi Tote",
               aliases=["túi tote", "túi vải", "tote"],
               vision_prompt="a tote bag (cloth/fabric bag with two handles, flat)"),
    GameObject(id="bowl",  name="cái tô nhựa", vi="cái tô nhựa",
               aliases=["tô", "chén", "bowl"],
               vision_prompt="a plastic bowl (round, colorful)"),
]

# 3 đội đối kháng.
TEAMS: list[Team] = [
    Team(id="A", name="Đội A", color="#e74c3c"),
    Team(id="B", name="Đội B", color="#3498db"),
    Team(id="C", name="Đội C", color="#2ecc71"),
]

# Điểm theo thứ tự về đích mỗi vòng (nhất/nhì/chót).
SCORE_BY_ORDER = [3, 2, 1]

ROUNDS = len(OBJECTS)      # 6 vòng = 6 vật phẩm (~5 phút)
RECOGNIZE_DEBOUNCE = 1.5   # giây chờ giữa các lần bấm nhận diện của 1 đội
# KHÔNG tự timeout mỗi vòng — ban tổ chức điều khiển tiến trình (Bỏ qua vòng / Vòng kế).
# Vòng kết thúc khi cả 3 đội nhận diện đúng (all_done) hoặc operator bấm skip/next.

# Số → chữ Việt cho TTS (Kokoro đọc CHỮ rõ hơn SỐ — tránh "Vòng 1" bị đoán sai).
# Đủ cho vòng (1-6) + điểm (0-18 = 6 vòng × 3).
_NUM_VI = ["không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín", "mười",
           "mười một", "mười hai", "mười ba", "mười bốn", "mười lăm", "mười sáu", "mười bảy", "mười tám"]


def num_vi(n) -> str:
    """1 → 'một', 15 → 'mười lăm'. Ngoài 0-18 thì trả str(n)."""
    try:
        return _NUM_VI[int(n)] if 0 <= int(n) < len(_NUM_VI) else str(n)
    except (TypeError, ValueError):
        return str(n)

# ---------- Thoại cố định (pre-cache TTS) ----------
# ORDER_WORD: hiển thị/khi đọc. ORDER_KEY: hậu tố key pre-cache (không dấu).
ORDER_WORD = {1: "nhất", 2: "nhì", 3: "ba"}
ORDER_KEY = {1: "nhat", 2: "nhi", 3: "ba"}

INTRO_TEXT = ("Xin chào các bạn nhỏ! Chào mừng đến với trò chơi Tìm Nắng Cùng AI! "
              "Mỗi vòng, AI sẽ gọi tên một vật phẩm. Các đội hãy bốc mù, giơ trước camera "
              "rồi bấm nút Nhận Diện. Đội nào đúng trước sẽ được điểm cao hơn. Bắt đầu nhé!")


def round_text(idx: int, obj: GameObject) -> str:
    return f"Vòng {num_vi(idx + 1)}! Các đội hãy tìm: {obj.name}! Nhanh lên nhé, ba, hai, một, bắt đầu!"


def correct_text(team_name: str, order: int) -> str:
    return f"{team_name} về {ORDER_WORD.get(order, order)}!"


def precache_lines() -> dict:
    """Nguồn sự thật duy nhất cho nội dung thoại cố định → gen pre-cache.
    Bao gồm: intro (1) + mở vòng (6, theo vật phẩm) + thông báo đúng/thứ tự (9, đội×thứ)."""
    lines = {"intro": INTRO_TEXT}
    for i, obj in enumerate(OBJECTS):
        lines[f"round_{obj.id}"] = round_text(i, obj)
    for t in TEAMS:
        for order in (1, 2, 3):
            lines[f"correct_{t.id}_{ORDER_KEY[order]}"] = correct_text(t.name, order)
    return lines
