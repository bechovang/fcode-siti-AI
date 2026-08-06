"""Hằng số dùng chung — tập trung magic numbers (trước đây rải rác 4 file).

TTS_SAMPLE_RATE từng hardcode ở 4 chỗ (server.py, timnang_master.py, 2 script gen);
OR_BASE từng là literal ở 2 server. Giờ định nghĩa 1 lần ở đây.
"""

TTS_SAMPLE_RATE = 24000          # Kokoro Vietnamese output sample rate
OR_BASE = "https://openrouter.ai/api/v1"
DEFAULT_MODEL = "openai/gpt-4o-mini"
DEFAULT_VOICE = "mai_linh"       # Kokoro giọng mặc định (14 giọng VN)
DEFAULT_GEN_ENGINE = "kokoro"    # engine gen pre-cache: kokoro | edge
DEFAULT_VOICE_EDGE = "vi-VN-HoaiMyNeural"
DEFAULT_RATE = "-5%"             # tốc độ edge-tts

FUZZY_THRESHOLD = 80             # rapidfuzz partial_ratio cho fuzzy match đáp án
TTS_TIMEOUT = 15                 # giây — timeout synthesize Kokoro (chống kẹt flow)

HOST = "0.0.0.0"
GAME1_PORT = 8000                # Cầu Vồng
GAME2_PORT = 8001                # Tìm Nắng
