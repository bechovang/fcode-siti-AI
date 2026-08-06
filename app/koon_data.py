"""Dữ liệu + kịch bản Trò 1 — Cầu Vồng. NGUỒN SỰ THẬT DUY NHẤT cho server + frontend.

Phase 2: CHALLENGES giờ là Pydantic Challenge (typed). Script động KOON
(INTRO_LINES/OUTRO_*/MAGIC_LINE — trước đây nằm trong server.py) được gộp vào đây
cho đúng "single source of truth" (trước đây đứt mạch giữa data module và server).
Âm thanh cố định pre-cache trong app/assets/audio/koon/.
"""
import os

from schemas.cau_vong import Challenge

APP_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(APP_DIR, "assets", "audio", "koon")
VIDEO_DIR = os.path.join(APP_DIR, "assets", "video")
RECAP_VIDEO = os.path.join(VIDEO_DIR, "recap.mp4")  # thả file vào đây khi có video recap thật

# Trình tự intro (phát lần lượt, chờ mỗi câu kết thúc)
INTRO = ["01_intro_greet", "02_intro_rainbow_q", "03_intro_lost_colors", "04_intro_rule", "05_intro_start"]
RECAP = "90_recap"
GOODBYE = "99_goodbye"

# 7 thử thách. aliases dùng cho fuzzy match dự phòng khi chưa có LLM.
CHALLENGES: list[Challenge] = [
    Challenge(n=1, color="Đỏ", hex="#e74c3c", q="q1_question", right="q1_right", wrong="q1_wrong",
              question_text="Trái gì càng chín càng đỏ, bên trong có rất nhiều hạt màu đen?",
              answer="dưa hấu", aliases=["trái dưa hấu", "qua dua ho", "dua hấu", "dưa"],
              hint="đó là một loại trái cây mùa hè, vỏ xanh ruột đỏ, căng mọng nước"),
    Challenge(n=2, color="Cam", hex="#e67e22", q="q2_question", right="q2_right", wrong="q2_wrong",
              question_text="Cái gì có 4 chân nhưng không biết đi?",
              answer="cái bàn", aliases=["bàn", "cai ban"],
              hint="đồ vật có bốn chân, các bạn ngồi học cùng nó mỗi ngày"),
    Challenge(n=3, color="Vàng", hex="#f1c40f", q="q3_question", right="q3_right", wrong="q3_wrong",
              question_text="Loài vật nào được mệnh danh là Chúa tể rừng xanh?",
              answer="sư tử", aliases=["su tu", "con sư tử"],
              hint="loài vật này có bờm to, được mệnh danh là chúa tể rừng xanh"),
    Challenge(n=4, color="Xanh lá", hex="#2ecc71", q="q4_question", right="q4_right", wrong="q4_wrong",
              question_text="Con gì mang ngôi nhà trên lưng?",
              answer="ốc sên", aliases=["oc sen", "sên"],
              hint="loài vật này di chuyển rất chậm, lúc nào cũng mang theo ngôi nhà của mình"),
    Challenge(n=5, color="Xanh dương", hex="#3498db", q="q5_question", right="q5_right", wrong="q5_wrong",
              question_text="Loài hoa nào luôn hướng về phía mặt trời?",
              answer="hoa hướng dương", aliases=["hướng dương", "huong duong"],
              hint="tên của loài hoa này đã nói lên đặc điểm, nó luôn quay về phía mặt trời"),
    Challenge(n=6, color="Chàm", hex="#6366f1", q="q6_question", right="q6_right", wrong="q6_wrong",
              question_text="Mùa nào trong năm thường có thời tiết nóng nhất?",
              answer="mùa hè", aliases=["hè", "mua he"],
              hint="mùa nóng nhất trong năm, các bạn được nghỉ học và đi chơi"),
    Challenge(n=7, color="Tím", hex="#9b59b6", q="q7_question", right="q7_right", wrong="q7_wrong",
              question_text="Sau cơn mưa, điều gì mà rất nhiều bạn nhỏ thích ngắm nhất trên bầu trời?",
              answer="cầu vồng", aliases=["cau vong", "vồng"],
              hint="đây là một dải màu rất đẹp thường xuất hiện trên bầu trời sau cơn mưa"),
]

RAINBOW_HEX = [c.hex for c in CHALLENGES]

# ---------- Kịch bản KOON (TTS động khi thiếu pre-cache) ----------
# Trước đây nằm trong server.py — giờ gộp vào đây cho đúng "single source of truth".
INTRO_LINES = [
    "Xin chào tất cả các bạn nhỏ! Tôi là Koon đây!",
    "Các bạn có biết không, trên bầu trời có một cầu vồng tuyệt đẹp với bảy sắc màu.",
    "Nhưng mà ông trời đã lấy mất bảy màu của cầu vồng rồi!",
    "Các bạn hãy giúp tôi tìm lại những mảnh màu đó nhé. Chúng ta sẽ cùng trả lời bảy câu hỏi thú vị!",
    "Các bạn đã sẵn sàng chưa? Cùng bắt đầu thôi!",
]

OUTRO_RECAP = (
    "Cảm ơn tất cả các bạn đã giúp Koon tìm lại đủ bảy sắc màu!"
    " Nhờ có các bạn mà cầu vồng lại rực rỡ trên bầu trời rồi!"
    " Bây giờ chúng mình cùng xem một đoạn phim thật đặc biệt nhé!"
)

MAGIC_LINE = (
    "Và bây giờ... cùng KOON ngắm điều kỳ diệu nhé!"
    " Các bạn nhắm mắt lại nào... Ba, hai, một... phép màu xuất hiện!"
)

OUTRO_GOODBYE = (
    "Cảm ơn các bạn thật nhiều! Koon rất vui khi được chơi cùng các bạn."
    " Hẹn gặp lại vào những lần sau nhé! Tạm biệt!"
)
