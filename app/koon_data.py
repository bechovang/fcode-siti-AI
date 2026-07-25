"""Dữ liệu kịch bản Trò 1 — Cùng Koon Đi Tìm Cầu Vồng.
Nguồn sự thật duy nhất cho server + frontend. Âm thanh đã pre-cache trong app/assets/audio/koon/.
"""
import os

APP_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(APP_DIR, "assets", "audio", "koon")

# Trình tự intro (phát lần lượt, chờ mỗi câu kết thúc)
INTRO = ["01_intro_greet", "02_intro_rainbow_q", "03_intro_lost_colors", "04_intro_rule", "05_intro_start"]
RECAP = "90_recap"
GOODBYE = "99_goodbye"

# 7 thử thách. aliases dùng cho fuzzy match dự phòng khi chưa có LLM.
CHALLENGES = [
    {"n": 1, "color": "Đỏ", "hex": "#e74c3c", "q": "q1_question", "right": "q1_right", "wrong": "q1_wrong",
     "question_text": "Trái gì càng chín càng đỏ, bên trong có rất nhiều hạt màu đen?",
     "answer": "dưa hấu", "aliases": ["trái dưa hấu", "qua dua ho", "dua hấu", "dưa"]},
    {"n": 2, "color": "Cam", "hex": "#e67e22", "q": "q2_question", "right": "q2_right", "wrong": "q2_wrong",
     "question_text": "Cái gì có 4 chân nhưng không biết đi?",
     "answer": "cái bàn", "aliases": ["bàn", "cai ban"]},
    {"n": 3, "color": "Vàng", "hex": "#f1c40f", "q": "q3_question", "right": "q3_right", "wrong": "q3_wrong",
     "question_text": "Loài vật nào được mệnh danh là Chúa tể rừng xanh?",
     "answer": "sư tử", "aliases": ["su tu", "con sư tử"]},
    {"n": 4, "color": "Xanh lá", "hex": "#2ecc71", "q": "q4_question", "right": "q4_right", "wrong": "q4_wrong",
     "question_text": "Con gì mang ngôi nhà trên lưng?",
     "answer": "ốc sên", "aliases": ["oc sen", "sên"]},
    {"n": 5, "color": "Xanh dương", "hex": "#3498db", "q": "q5_question", "right": "q5_right", "wrong": "q5_wrong",
     "question_text": "Loài hoa nào luôn hướng về phía mặt trời?",
     "answer": "hoa hướng dương", "aliases": ["hướng dương", "huong duong"]},
    {"n": 6, "color": "Chàm", "hex": "#34495e", "q": "q6_question", "right": "q6_right", "wrong": "q6_wrong",
     "question_text": "Mùa nào trong năm thường có thời tiết nóng nhất?",
     "answer": "mùa hè", "aliases": ["hè", "mua he"]},
    {"n": 7, "color": "Tím", "hex": "#9b59b6", "q": "q7_question", "right": "q7_right", "wrong": "q7_wrong",
     "question_text": "Sau cơn mưa, điều gì mà rất nhiều bạn nhỏ thích ngắm nhất trên bầu trời?",
     "answer": "cầu vồng", "aliases": ["cau vong", "vồng"]},
]

RAINBOW_HEX = [c["hex"] for c in CHALLENGES]
