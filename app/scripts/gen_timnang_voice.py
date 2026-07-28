"""
Pre-cache giọng Trò 2 (Tìm Nắng Cùng AI) — engine Kokoro (mặc định) hoặc edge-tts (backup).
Chạy:  python app/scripts/gen_timnang_voice.py
Chọn engine:  KOON_GEN_ENGINE=kokoro (mặc định)  |  KOON_GEN_ENGINE=edge
  - kokoro: Kokoro-Vietnamese (ONNX CPU), giọng `mai_linh` → .wav 24kHz (nhất quán với TTS động).
  - edge:   edge-tts vi-VN-HoaiMyNeural (cần mạng, free) → .mp3 (backup tier thấp hơn).

Output: app/assets/audio/timnang/<key>.{wav|mp3} — phát tức thì (<200ms) khi mở vòng / thông báo đúng.

Nội dung thoại lấy từ timnang_data.precache_lines() (nguồn sự thật duy nhất):
  intro (1) + mở vòng (6, theo vật phẩm) + thông báo đúng/thứ tự (9, đội×thứ) = 16 file.
"""
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")  # Windows console mặc định cp1252 → crash khi in tiếng Việt
except Exception:
    pass

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import timnang_data as D

ENGINE = os.environ.get("KOON_GEN_ENGINE", "kokoro").strip().lower()
OUT = D.AUDIO_DIR
LINES = D.precache_lines()


# ---------------------------------------------------------------- Kokoro (.wav)
def gen_kokoro():
    import soundfile as sf
    from kokoro_vietnamese import KokoroVietnamese as KokoroTTS

    voice = os.environ.get("KOON_VOICE", "mai_linh")
    tts = KokoroTTS(device="cpu", voice=voice)
    os.makedirs(OUT, exist_ok=True)
    ok, fail = 0, 0
    for key, text in LINES.items():
        path = os.path.join(OUT, f"{key}.wav")
        try:
            audio, _phonemes = tts.synthesize(text)
            sf.write(path, audio, 24000)
            print(f"OK   {key}")
            ok += 1
        except Exception as e:
            print(f"FAIL {key}: {e}")
            fail += 1
    print(f"\nKokoro [{voice}] xong: {ok} OK, {fail} FAIL — output: {OUT}")
    if fail:
        sys.exit(1)


# ------------------------------------------------------------------ edge (.mp3)
def gen_edge():
    import asyncio
    import edge_tts

    VOICE = os.environ.get("KOON_VOICE_EDGE", "vi-VN-HoaiMyNeural")
    RATE = os.environ.get("KOON_RATE", "-5%")

    async def _run():
        os.makedirs(OUT, exist_ok=True)
        ok, fail = 0, 0
        for key, text in LINES.items():
            path = os.path.join(OUT, f"{key}.mp3")
            try:
                comm = edge_tts.Communicate(text, VOICE, rate=RATE)
                await comm.save(path)
                print(f"OK   {key}")
                ok += 1
            except Exception as e:
                print(f"FAIL {key}: {e}")
                fail += 1
        print(f"\nEdge [{VOICE}] xong: {ok} OK, {fail} FAIL — output: {OUT}")
        if fail:
            sys.exit(1)

    asyncio.run(_run())


if __name__ == "__main__":
    print(f"Engine: {ENGINE}  |  {len(LINES)} dòng thoại  |  output dir: {OUT}")
    if ENGINE == "edge":
        gen_edge()
    elif ENGINE == "kokoro":
        gen_kokoro()
    else:
        print(f"ENGINE không hợp lệ: {ENGINE} (dùng 'kokoro' hoặc 'edge')")
        sys.exit(2)
