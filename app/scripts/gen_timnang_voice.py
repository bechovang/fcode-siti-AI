"""
Pre-cache giọng Trò 2 (Tìm Nắng Cùng AI) — engine Kokoro (mặc định) hoặc edge-tts (backup).
Chạy:  python app/scripts/gen_timnang_voice.py
Chọn engine:  KOON_GEN_ENGINE=kokoro (mặc định)  |  KOON_GEN_ENGINE=edge
  - kokoro: Kokoro-Vietnamese (ONNX CPU), giọng `mai_linh` → .wav 24kHz (nhất quán với TTS động).
  - edge:   edge-tts vi-VN-HoaiMyNeural (cần mạng, free) → .mp3 (backup tier thấp hơn).

Output: app/assets/audio/timnang/<key>.{wav|mp3} — phát tức thì (<200ms) khi mở vòng / thông báo đúng.

Nội dung thoại lấy từ timnang_data.precache_lines() (nguồn sự thật duy nhất):
  intro (1) + mở vòng (6, theo vật phẩm) + thông báo đúng/thứ tự (9, đội×thứ) = 16 file.
Logic gen (Kokoro/edge loop, ok/fail, exit) nằm trong _voice_gen_core (share với Trò 1).
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))   # app/ → timnang_data
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))                        # scripts/ → _voice_gen_core
import timnang_data as D
from _voice_gen_core import run_engine

ENGINE = os.environ.get("KOON_GEN_ENGINE", "kokoro").strip().lower()
OUT = D.AUDIO_DIR
LINES = D.precache_lines()


if __name__ == "__main__":
    run_engine(ENGINE, LINES, OUT)   # Trò 2 không cần normalize
