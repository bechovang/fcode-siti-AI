"""Shared logic cho 2 script gen pre-cache giọng (gen_koon_voice, gen_timnang_voice).

Trước đây 2 script ~85% giống nhau: gen_kokoro() / gen_edge() / __main__ dispatch
copy-paste, chỉ khác LINES + OUT + _normalize (KOON→Cun). File này gộp logic chung;
2 script giờ chỉ còn LINES + OUT (+ normalize tuỳ chọn) rồi gọi run_engine().

Self-contained (không import core) để script chạy đúng kể cả khi chỉ scripts/ trên path.
TTS_SAMPLE_RATE đồng bộ với core.constants.TTS_SAMPLE_RATE (Phase 2 sẽ gộp khi thành package).
"""
import asyncio
import os
import sys

# Windows console mặc định cp1252 → crash khi in tiếng Việt. Chạy 1 lần lúc import.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

TTS_SAMPLE_RATE = 24000   # == core.constants.TTS_SAMPLE_RATE (Kokoro output rate)


def _kokoro_voice() -> str:
    return os.environ.get("KOON_VOICE", "mai_linh")


def _edge_voice() -> str:
    return os.environ.get("KOON_VOICE_EDGE", "vi-VN-HoaiMyNeural")


def _edge_rate() -> str:
    return os.environ.get("KOON_RATE", "-5%")


def gen_kokoro(lines: dict, out_dir: str, normalize=None) -> None:
    """Synthesize từng dòng bằng Kokoro → <out_dir>/<key>.wav. sys.exit(1) nếu có FAIL.

    normalize: hàm tùy chọn biến đổi text trước khi synthesize (vd KOON→Cun)."""
    import soundfile as sf
    from kokoro_vietnamese import KokoroVietnamese as KokoroTTS

    voice = _kokoro_voice()
    tts = KokoroTTS(device="cpu", voice=voice)
    os.makedirs(out_dir, exist_ok=True)
    ok, fail = 0, 0
    for key, text in lines.items():
        path = os.path.join(out_dir, f"{key}.wav")
        try:
            t = normalize(text) if normalize else text
            audio, _phonemes = tts.synthesize(t)
            sf.write(path, audio, TTS_SAMPLE_RATE)
            print(f"OK   {key}")
            ok += 1
        except Exception as e:
            print(f"FAIL {key}: {e}")
            fail += 1
    print(f"\nKokoro [{voice}] xong: {ok} OK, {fail} FAIL — output: {out_dir}")
    if fail:
        sys.exit(1)


def gen_edge(lines: dict, out_dir: str, normalize=None) -> None:
    """Synthesize từng dòng bằng edge-tts → <out_dir>/<key>.mp3. sys.exit(1) nếu có FAIL."""
    import edge_tts

    voice = _edge_voice()
    rate = _edge_rate()

    async def _run():
        os.makedirs(out_dir, exist_ok=True)
        ok, fail = 0, 0
        for key, text in lines.items():
            path = os.path.join(out_dir, f"{key}.mp3")
            try:
                t = normalize(text) if normalize else text
                comm = edge_tts.Communicate(t, voice, rate=rate)
                await comm.save(path)
                print(f"OK   {key}")
                ok += 1
            except Exception as e:
                print(f"FAIL {key}: {e}")
                fail += 1
        print(f"\nEdge [{voice}] xong: {ok} OK, {fail} FAIL — output: {out_dir}")
        if fail:
            sys.exit(1)

    asyncio.run(_run())


def run_engine(engine: str, lines: dict, out_dir: str, normalize=None) -> None:
    """Dispatch theo engine (kokoro | edge). In thông tin + gọi gen tương ứng."""
    print(f"Engine: {engine}  |  {len(lines)} dòng thoại  |  output dir: {out_dir}")
    if engine == "edge":
        gen_edge(lines, out_dir, normalize)
    elif engine == "kokoro":
        gen_kokoro(lines, out_dir, normalize)
    else:
        print(f"ENGINE không hợp lệ: {engine} (dùng 'kokoro' hoặc 'edge')")
        sys.exit(2)
