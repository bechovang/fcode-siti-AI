"""Dữ liệu Trò 2 — Tìm Nắng Cùng AI (đối kháng N đội, nhận diện đồ vật).
Nguồn sự thật cho master + stations + gen pre-cache TTS.

Số đội (2–6) thao tác được từ web UI của operator (R8); thang điểm động:
N đội thì vị trí 1..N nhận N..1 điểm.
"""
import os

APP_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(APP_DIR, "static", "timnang")
AUDIO_DIR = os.path.join(APP_DIR, "assets", "audio", "timnang")  # pre-cache TTS (gitignored)

# 6 vật phẩm cần tìm. aliases không dùng cho vision (vision chấm ảnh) — giữ để
# tham khảo/hiển thị. vision_prompt = mô tả tiếng Anh cho GPT-4o-mini. icon cho UI.
OBJECTS = [
    {"id": "ball",  "name": "quả bóng tennis", "vi": "quả bóng tennis", "icon": "🎾",
     "aliases": ["bóng tennis", "quả bóng", "tennis"],
     "vision_prompt": "a tennis ball (small, yellow-green, fuzzy)"},
    {"id": "lavie", "name": "chai nước Lavie", "vi": "chai nước Lavie", "icon": "🧴",
     "aliases": ["lavie", "nước lavie", "chai nước"],
     "vision_prompt": "a plastic bottle of Lavie mineral water (clear bottle, blue label, Vietnamese brand)"},
    {"id": "coke",  "name": "chai Coca-Cola", "vi": "chai Coca-Cola", "icon": "🥤",
     "aliases": ["coca", "coca-cola", "coke"],
     "vision_prompt": "a Coca-Cola bottle or can (red label, Coca-Cola brand)"},
    {"id": "spoon", "name": "cái muỗng", "vi": "cái muỗng", "icon": "🥄",
     "aliases": ["muỗng", "thìa", "spoon"],
     "vision_prompt": "a spoon (eating utensil)"},
    {"id": "tote",  "name": "túi Tote", "vi": "túi Tote", "icon": "🛍️",
     "aliases": ["túi tote", "túi vải", "tote"],
     "vision_prompt": "a tote bag (cloth/fabric bag with two handles, flat)"},
    {"id": "bowl",  "name": "cái tô nhựa", "vi": "cái tô nhựa", "icon": "🥣",
     "aliases": ["tô", "chén", "bowl"],
     "vision_prompt": "a plastic bowl (round, colorful)"},
]

# Pool 6 đội (operator chọn 2–6 từ web). Màu được chọn để tương phản tốt trên
# nền tối sân khấu (D = cam thay vì vàng khó đọc; F = teal cho đội thứ 6).
ALL_TEAMS = [
    {"id": "A", "name": "Đội A", "color": "#e74c3c"},  # đỏ
    {"id": "B", "name": "Đội B", "color": "#3498db"},  # xanh dương
    {"id": "C", "name": "Đội C", "color": "#2ecc71"},  # xanh lá
    {"id": "D", "name": "Đội D", "color": "#e67e22"},  # cam
    {"id": "E", "name": "Đội E", "color": "#9b59b6"},  # tím
    {"id": "F", "name": "Đội F", "color": "#1abc9c"},  # teal
]
TEAM_POOL = ALL_TEAMS  # alias (tên cũ)
VALID_TEAM_IDS = [t["id"] for t in ALL_TEAMS]

MIN_TEAMS = 2
MAX_TEAMS = len(ALL_TEAMS)   # 6
DEFAULT_TEAMS = 3


def get_teams(count: int = DEFAULT_TEAMS):
    """Trả `count` đội đầu tiên (kẹp trong [MIN, MAX]). Dùng khi khởi tạo từ env."""
    count = max(MIN_TEAMS, min(MAX_TEAMS, int(count)))
    return ALL_TEAMS[:count]


# Số đội khi boot (env TEAMS_COUNT có thể ghi đè; operator đổi lại được từ web).
TEAMS = get_teams(int(os.environ.get("TEAMS_COUNT", str(DEFAULT_TEAMS))))


def score_for_order(order: int, n_teams: int) -> int:
    """Thang điểm động: vị trí 1..N nhận N..1 điểm (5 đội → 5/4/3/2/1)."""
    if 1 <= order <= n_teams:
        return n_teams - order + 1
    return 0


# alias tương thích với code cũ / naipret
get_points_by_order = score_for_order
SCORE_BY_ORDER = None  # giữ tên để import không lỗi (không dùng nữa)


ROUNDS = len(OBJECTS)      # 6 vòng = 6 vật phẩm (~5 phút)
RECOGNIZE_DEBOUNCE = 1.5   # giây chờ giữa các lần bấm nhận diện của 1 đội

# Số → chữ tiếng Việt (đủ cho tổng điểm tối đa: 6 vòng × 6 = 36). Lưu ý "21" đọc
# là "hai mốt" (không phải "hai mươi mốt"), "25" là "hai lăm" (chuẩn).
_NUM_VI = [
    "không", "một", "hai", "ba", "bốn", "năm", "sáu", "bảy", "tám", "chín",
    "mười", "mười một", "mười hai", "mười ba", "mười bốn", "mười lăm",
    "mười sáu", "mười bảy", "mười tám", "mười chín",
    "hai mươi", "hai mốt", "hai hai", "hai ba", "hai tư", "hai lăm",
    "hai sáu", "hai bảy", "hai tám", "hai chín",
    "ba mươi", "ba mốt", "ba hai", "ba ba", "ba tư", "ba lăm", "ba mươi sáu",
]


def num_vi(n) -> str:
    """1 → 'một', 15 → 'mười lăm', 21 → 'hai mốt'. Trả str(n) nếu ngoài dải."""
    try:
        i = int(n)
        return _NUM_VI[i] if 0 <= i < len(_NUM_VI) else str(i)
    except (TypeError, ValueError):
        return str(n)


# ---------- Thoại cố định (pre-cache TTS) ----------
ORDER_WORD = {1: "nhất", 2: "nhì", 3: "ba", 4: "tư", 5: "năm", 6: "sáu"}
ORDER_KEY = {1: "nhat", 2: "nhi", 3: "ba", 4: "tu", 5: "nam", 6: "sau"}

INTRO_TEXT = ("Xin chào các bạn nhỏ! Chào mừng đến với trò chơi Tìm Nắng Cùng AI! "
              "Mỗi vòng, AI sẽ gọi tên một vật phẩm. Các đội hãy bốc mù, giơ trước camera "
              "rồi bấm nút Nhận Diện. Đội nào đúng trước sẽ được điểm cao hơn. Bắt đầu nhé!")


def round_text(idx: int, obj: dict) -> str:
    return f"Vòng {num_vi(idx + 1)}! Các đội hãy tìm: {obj['name']}! Nhanh lên nhé, ba, hai, một, bắt đầu!"


def correct_text(team_name: str, order: int) -> str:
    return f"{team_name} về {ORDER_WORD.get(order, order)}!"


def precache_lines() -> dict:
    """Nguồn sự thật duy nhất cho nội dung thoại cố định → gen pre-cache."""
    lines = {"intro": INTRO_TEXT}
    for i, obj in enumerate(OBJECTS):
        lines[f"round_{obj['id']}"] = round_text(i, obj)
    for t in ALL_TEAMS:
        for order in range(1, MAX_TEAMS + 1):
            lines[f"correct_{t['id']}_{ORDER_KEY[order]}"] = correct_text(t["name"], order)
    return lines
