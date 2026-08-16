"""Dữ liệu Trò 2 — Tìm Nắng Cùng AI (đối kháng 2–6 đội, nhận diện đồ vật).
Nguồn sự thật cho master + stations + gen pre-cache TTS.
"""
import os

APP_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(APP_DIR, "static", "timnang")
AUDIO_DIR = os.path.join(APP_DIR, "assets", "audio", "timnang")  # pre-cache TTS (gitignored)

# 6 vật phẩm cần tìm. aliases không dùng cho vision (vision chấm ảnh) — giữ để
# tham khảo/hiển thị. vision_prompt = mô tả tiếng Anh cho GPT-4o-mini.
OBJECTS = [
    {"id": "ball",  "name": "quả bóng tennis", "vi": "quả bóng tennis",
     "aliases": ["bóng tennis", "quả bóng", "tennis"],
     "vision_prompt": "a tennis ball (small, yellow-green, fuzzy)"},
    {"id": "bottle", "name": "chai nước", "vi": "chai nước",
     "aliases": ["chai nước", "chai nước suối", "chai nước khoáng", "nước suối", "nước khoáng", "nước", "chai nước lọc", "water bottle", "lavie", "aquafina", "dasani"],
     "vision_prompt": "a plastic water bottle or mineral water bottle of any brand (clear or colored plastic drinking water bottle, Lavie, Aquafina, Dasani, TH True Water, or generic water bottle)"},
    {"id": "can",    "name": "lon nước", "vi": "lon nước",
     "aliases": ["lon nước", "lon nước ngọt", "lon nước giải khát", "lon monster", "lon coca", "lon pepsi", "lon nước tăng lực", "lon red bull", "can", "soda can", "energy drink can"],
     "vision_prompt": "an aluminum beverage can, soda can, or energy drink can of any brand (e.g. Monster Energy, Coca-Cola, Pepsi, Red Bull, Sprite, 7Up, or any canned drink)"},
    {"id": "spoon", "name": "cái muỗng", "vi": "cái muỗng",
     "aliases": ["muỗng", "thìa", "spoon"],
     "vision_prompt": "a spoon (eating utensil)"},
    {"id": "tote",  "name": "túi Tote", "vi": "túi Tote",
     "aliases": ["túi tote", "túi vải", "tote"],
     "vision_prompt": "a tote bag (cloth/fabric bag with two handles, flat)"},
    {"id": "bowl",  "name": "cái tô nhựa", "vi": "cái tô nhựa",
     "aliases": ["tô", "chén", "bowl"],
     "vision_prompt": "a plastic bowl (round, colorful)"},
]

# Bể đội: tối đa 6 (A-F). Trò chơi dùng N đội đầu tiên (N do operator chọn trên web,
# 2 ≤ N ≤ 6). Màu phải khớp TEAM_COLORS ở station.html / master.html.
TEAMS = [
    {"id": "A", "name": "Đội A", "color": "#e74c3c"},
    {"id": "B", "name": "Đội B", "color": "#3498db"},
    {"id": "C", "name": "Đội C", "color": "#2ecc71"},
    {"id": "D", "name": "Đội D", "color": "#9b59b6"},
    {"id": "E", "name": "Đội E", "color": "#e67e22"},
    {"id": "F", "name": "Đội F", "color": "#1abc9c"},
]

MIN_TEAMS, MAX_TEAMS, DEFAULT_TEAMS = 2, 6, 3


def score_for_order(order: int, team_count: int) -> int:
    """N đội: về nhất +N, nhì +N-1, ..., chót +1. (vd 5 đội → 5/4/3/2/1.)"""
    return max(1, team_count - order + 1)


# Giữ lại cho tham khảo; master.py giờ dùng score_for_order động theo team_count.
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
# Đủ cho tối đa 6 đội (hạng 1-6).
ORDER_WORD = {1: "nhất", 2: "nhì", 3: "ba", 4: "tư", 5: "năm", 6: "sáu"}
ORDER_KEY  = {1: "nhat", 2: "nhi", 3: "ba", 4: "tu", 5: "nam", 6: "sau"}

INTRO_TEXT = ("Xin chào các bạn nhỏ! Chào mừng đến với trò chơi Tìm Nắng Cùng AI! "
              "Mỗi vòng, AI sẽ gọi tên một vật phẩm. Các đội hãy bốc mù, giơ trước camera "
              "rồi bấm nút Nhận Diện. Đội nào đúng trước sẽ được điểm cao hơn. Bắt đầu nhé!")


def round_text(idx: int, obj: dict) -> str:
    return f"Vòng {num_vi(idx + 1)}! Các đội hãy tìm: {obj['name']}! Nhanh lên nhé, ba, hai, một, bắt đầu!"


def correct_text(team_name: str, order: int) -> str:
    return f"{team_name} về {ORDER_WORD.get(order, order)}!"


def precache_lines() -> dict:
    """Nguồn sự thật duy nhất cho nội dung thoại cố định → gen pre-cache.
    Bao gồm: intro (1) + mở vòng (6, theo vật phẩm) + thông báo đúng/thứ tự
    (6 đội × 6 hạng = 36) — gen hết cho MAX_TEAMS để mọi N đội đều có sẵn file phát tức thì."""
    lines = {"intro": INTRO_TEXT}
    for i, obj in enumerate(OBJECTS):
        lines[f"round_{obj['id']}"] = round_text(i, obj)
    for t in TEAMS:
        for order in range(1, MAX_TEAMS + 1):
            lines[f"correct_{t['id']}_{ORDER_KEY[order]}"] = correct_text(t["name"], order)
    return lines
