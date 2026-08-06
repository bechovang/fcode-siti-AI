"""Pre-cache giọng KOON bằng CapCut TTS (giọng BV421_vivn_streaming 'Nhỏ Ngọt Ngào' — vi-VN).
Pure Python, không cần GPU/key. Lưu ý: API CapCut trả status 'succeed' (SDK gốc bị bug kiểm 'success'
nên phải poll thủ công). Batch tất cả câu trong 1 task.

Chạy:  python app/scripts/gen_koon_voice_capcut.py
"""
import json
import os
import sys
import time
from pathlib import Path

import requests

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))                                   # để import LINES
sys.path.insert(0, str(HERE.parent.parent / "ref" / "capcut-tts-api"))
from capcut_tts_api import CapCutClient
from gen_koon_voice import LINES  # dùng chung dict câu thoại

VOICE = os.environ.get("CAPCUT_VOICE", "BV421_vivn_streaming")  # Nhỏ Ngọt Ngào (vi-VN)
OUT = HERE.parent / "assets" / "audio" / "koon"
OUT.mkdir(parents=True, exist_ok=True)


def clean(t):
    return t.replace("KOON", "Cun")  # phát âm tên nhân vật là "Cun"


def main():
    c = CapCutClient()
    keys = list(LINES.keys())
    texts = [clean(LINES[k]) for k in keys]
    print(f"Batch {len(texts)} câu | voice={VOICE}")

    cr = c.create_tts_task(texts, VOICE, None, "1.0")
    tasks = (cr.get("data") or {}).get("tasks") or []
    if not tasks:
        print("Không tạo được task:", cr)
        sys.exit(1)
    t = tasks[0]
    tid, tok = t["id"], t["token"]
    print("Poll đến 'succeed' (tối đa ~4 phút)...")
    subs = None
    for i in range(60):
        qr = c.query_tts_task(tid, tok)
        qt = (qr.get("data") or {}).get("tasks") or [{}]
        st = qt[0].get("status")
        if st == "succeed":
            subs = json.loads(qt[0]["payload"]).get("audio_subtitles", [])
            print(f"Succeed ~{i*4}s — {len(subs)} audio trả về.")
            break
        if st == "failed":
            print("Task FAILED:", qt[0])
            sys.exit(1)
        time.sleep(4)
    if not subs:
        print("Timeout — task không xong kịp.")
        sys.exit(1)
    if len(subs) != len(keys):
        print(f"CẢNH BÁO: {len(subs)} audio ≠ {len(keys)} câu — map theo index.")

    ok = 0
    for idx, key in enumerate(keys):
        if idx >= len(subs):
            print(f"  THIẾU: {key}")
            continue
        url = subs[idx].get("speech_url")
        if not url:
            print(f"  KHÔNG có url: {key}")
            continue
        try:
            r = requests.get(url, timeout=60)
            if r.status_code == 200:
                (OUT / f"{key}.mp3").write_bytes(r.content)
                print(f"  OK   {key} ({len(r.content)//1024} KB)")
                ok += 1
            else:
                print(f"  LỖI tải {key}: HTTP {r.status_code}")
        except Exception as e:
            print(f"  LỖI {key}: {e}")
    print(f"\nXong: {ok}/{len(keys)} → {OUT}")


if __name__ == "__main__":
    main()
