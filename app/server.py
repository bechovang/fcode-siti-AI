"""Server trò Cầu Vồng (KOON) — FastAPI + WebSocket + Kokoro TTS.
- Kokoro Vietnamese TTS (ONNX CPU): sinh giọng nói động, không cần pre-cache.
- KOON nói tự nhiên, lễ phép, đúng ngữ cảnh với từng câu trả lời của trẻ.
- 7 thử thách, chấm đáp án LLM/fuzzy, operator controls.

Backlog:
  - STT (PhoWhisper): frontend stream audio -> endpoint /asr.
  - Live2D KOON: frontend (pixi-live2d-display), sync lip-sync với audio.
  - Khử ồn DSP: tiền xử lý audio trước khi vào STT.
"""
import os
import sys
import json
import asyncio
import logging
import tempfile
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import koon_data as K

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from rapidfuzz import fuzz
import soundfile as sf

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("koon")

APP_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(APP_DIR, "static")
TTS_DIR = tempfile.mkdtemp(prefix="koon_tts_")
log.info("TTS temp dir: %s", TTS_DIR)

# ---------- OpenRouter LLM judge ----------
OR_KEY = os.environ.get("OPENROUTER_API_KEY", "").strip()
OR_BASE = "https://openrouter.ai/api/v1"
OR_MODEL = os.environ.get("OR_MODEL", "openai/gpt-4o-mini")
llm = OpenAI(base_url=OR_BASE, api_key=OR_KEY) if OR_KEY else None
log.info("LLM judge: %s", "OpenRouter " + OR_MODEL if llm else "TẮT — dùng fuzzy match")

# ---------- Kokoro Vietnamese TTS (ONNX CPU) ----------
_tts = None
TTS_AVAILABLE = False
try:
    from kokoro_vietnamese import KokoroVietnamese as KokoroTTS
    TTS_AVAILABLE = True
except ImportError:
    log.warning("kokoro-vietnamese chưa cài — chạy pip install -e .[onnx] trong ref/Kokoro-Vietnamese")


def get_tts():
    global _tts
    if not TTS_AVAILABLE:
        return None
    if _tts is None:
        voice = os.environ.get("KOON_VOICE", "mai_linh")
        _tts = KokoroTTS(device="cpu", voice=voice)
        log.info("Kokoro TTS sẵn sàng (giọng %s, device=cpu)", voice)
    return _tts


# Khởi tạo TTS từ đầu để load model ngay
_ = get_tts()

# ---------- judge ----------
def judge_fuzzy(text: str, ch: dict) -> bool:
    t = (text or "").strip().lower()
    if not t:
        return False
    cands = [ch["answer"]] + ch.get("aliases", [])
    return any(fuzz.partial_ratio(t, c) >= 80 for c in cands)


def judge_llm(text: str, ch: dict):
    if not llm:
        return None
    sysp = ("Bạn là trọng tài trò chơi trẻ em tiếng Việt. Quyết định câu trả lời của bé ĐÚNG hay SAI với đáp án. "
            "Chỉ trả lời JSON hợp lệ: {\"correct\": true} hoặc {\"correct\": false}. "
            "Chấp nhận sai chính tả, không dấu, từ đồng nghĩa, thêm từ lễ phép (dạ, ạ).")
    usrp = f"Đáp án đúng: '{ch['answer']}'. Câu bé nói: '{text}'."
    try:
        r = llm.chat.completions.create(
            model=OR_MODEL,
            messages=[{"role": "system", "content": sysp}, {"role": "user", "content": usrp}],
            temperature=0,
        )
        data = json.loads(r.choices[0].message.content.strip())
        return bool(data.get("correct"))
    except Exception as e:
        log.warning("LLM judge lỗi (%s) -> dùng fuzzy", e)
        return None


def judge(text: str, ch: dict) -> bool:
    if llm:
        v = judge_llm(text, ch)
        if v is not None:
            return v
    return judge_fuzzy(text, ch)


# ---------- STT (faster-whisper, tiếng Việt) ----------
_whisper = None


def get_whisper():
    global _whisper
    if _whisper is None:
        from faster_whisper import WhisperModel
        mname = os.environ.get("WHISPER_MODEL", "diepho/PhoWhisper-small-ct2")
        log.info("Load Whisper '%s' (CPU int8) — ~20s lần đầu...", mname)
        _whisper = WhisperModel(mname, device="cpu", compute_type="int8")
        log.info("Whisper sẵn sàng.")
    return _whisper


def transcribe_path(path: str) -> str:
    m = get_whisper()
    vocab = ", ".join(ch["answer"] for ch in K.CHALLENGES)
    prompt = f"Trò chơi đố vui cho trẻ em tiếng Việt. Một số từ thường gặp: {vocab}."
    segs, _ = m.transcribe(
        path,
        language="vi",
        beam_size=1,
        vad_filter=True,
        initial_prompt=prompt,
        condition_on_previous_text=False,
        no_speech_threshold=0.6,
    )
    return " ".join(s.text for s in segs).strip()


# ---------- app ----------
app = FastAPI()
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ---------- session / flow ----------
class Session:
    def __init__(self, ws: WebSocket):
        self.ws = ws
        self.phase = "idle"
        self.idx = 0
        self.unlocked = []
        self.flow_task = None
        self._audio_done = asyncio.Event()
        self._answer = None
        self._answer_ready = asyncio.Event()
        self._op = None  # skip | force_correct | replay
        # Duy trì các file TTS đang phát để cleanup sau
        self._active_tts_files: list[str] = []

    async def send(self, msg: dict):
        await self.ws.send_text(json.dumps(msg, ensure_ascii=False))

    async def play(self, key: str):
        """Phát audio pre-cached (MP3 từ thư mục assets)."""
        self._audio_done.clear()
        await self.send({"type": "play_audio", "key": key})
        await self._audio_done.wait()

    async def say(self, text: str):
        """Phát text qua Kokoro TTS (sinh động, WAV), chờ kết thúc."""
        tts = get_tts()
        if not tts:
            log.warning("TTS không có — bỏ qua: '%s'", text[:50])
            return

        # Sinh audio trong thread riêng để không block event loop
        audio, phonemes = await asyncio.to_thread(tts.synthesize, text)
        key = f"tts_{uuid.uuid4().hex}"
        wav_path = os.path.join(TTS_DIR, f"{key}.wav")
        sf.write(wav_path, audio, 24000)
        log.debug("TTS [%s] '%s' | phonemes: %s", key, text[:50], phonemes)

        self._active_tts_files.append(wav_path)
        self._audio_done.clear()
        await self.send({"type": "play_audio", "key": key, "tts": True})
        await self._audio_done.wait()

        # Dọn file sau khi frontend phát xong
        try:
            os.unlink(wav_path)
            self._active_tts_files.remove(wav_path)
        except (OSError, ValueError):
            pass

    async def state(self):
        await self.send({
            "type": "state",
            "phase": self.phase,
            "idx": self.idx,
            "unlocked": self.unlocked,
            "total": len(K.CHALLENGES),
        })


# ---------- kịch bản KOON với TTS động ----------
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

OUTRO_GOODBYE = (
    "Cảm ơn các bạn thật nhiều! Koon rất vui khi được chơi cùng các bạn."
    " Hẹn gặp lại vào những lần sau nhé! Tạm biệt!"
)


async def run_flow(s: Session):
    """Chạy kịch bản 7 thử thách với TTS động."""
    try:
        # ---- INTRO ----
        s.phase = "intro"
        await s.state()
        for line in INTRO_LINES:
            if s._op == "skip":
                s._op = None
                break
            await s.say(line)

        # ---- 7 THỬ THÁCH ----
        for i, ch in enumerate(K.CHALLENGES):
            s.idx = i
            s.phase = "ask"
            await s.state()
            await s.send({
                "type": "show_question",
                "text": ch["question_text"],
                "color": ch["color"],
                "hex": ch["hex"],
            })

            while True:  # vòng lặp thử lại khi sai
                if s._op == "skip":
                    s._op = None
                    break

                # KOON đọc câu hỏi
                await s.say(
                    f"Câu hỏi thứ {ch['n']} màu {ch['color'].lower()}: "
                    f"{ch['question_text']}"
                )

                if s._op == "replay":
                    s._op = None
                    continue
                if s._op == "skip":
                    s._op = None
                    break

                # Chờ trẻ trả lời
                s.phase = "await"
                await s.state()
                await s.send({"type": "await_answer"})
                s._answer_ready.clear()
                s._answer = None
                await s._answer_ready.wait()

                ans = s._answer or ""
                if s._op == "force_correct":
                    s._op = None
                    correct = True
                else:
                    correct = judge(ans, ch)

                log.info("Thử thách %d: '%s' -> %s", ch["n"], ans, "ĐÚNG" if correct else "SAI")
                s.phase = "feedback"
                await s.state()

                if correct:
                    await s.say(
                        f"Chính xác! Đáp án là {ch['answer']}."
                        f" Các bạn giỏi quá! Mảnh màu {ch['color'].lower()} đã được tìm thấy!"
                    )
                    s.unlocked.append(ch["hex"])
                    await s.send({"type": "unlock_color", "hex": ch["hex"]})
                    break
                else:
                    await s.say(
                        f"Chưa đúng rồi các bạn ơi!"
                        f" Gợi ý nhé: {ch['hint']}."
                        f" Các bạn thử lại xem?"
                    )

        # ---- RAINBOW ----
        s.phase = "rainbow"
        await s.state()
        await s.send({"type": "rainbow"})
        await asyncio.sleep(4)

        # ---- RECAP ----
        s.phase = "recap"
        await s.state()
        await s.say(OUTRO_RECAP)

        # ---- DONE ----
        s.phase = "done"
        await s.state()
        await s.say(OUTRO_GOODBYE)
        log.info("Hoàn thành show.")

    except asyncio.CancelledError:
        raise


# ---------- WebSocket ----------
@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    s = Session(ws)

    async def start():
        if s.flow_task and not s.flow_task.done():
            s.flow_task.cancel()
        s.idx = 0
        s.unlocked = []
        s._op = None
        s._answer = None
        await s.send({"type": "reset"})
        s.flow_task = asyncio.create_task(run_flow(s))

    await s.send({"type": "ready"})
    try:
        while True:
            msg = json.loads(await ws.receive_text())
            t = msg.get("type")
            if t == "start":
                await start()
            elif t == "audio_ended":
                s._audio_done.set()
            elif t == "answer":
                s._answer = msg.get("text", "")
                s._answer_ready.set()
            elif t == "op":
                a = msg.get("action")
                if a == "restart":
                    await start()
                else:  # skip | force_correct | replay
                    s._op = a
    except WebSocketDisconnect:
        log.info("WS ngắt")
        if s.flow_task:
            s.flow_task.cancel()


# ---------- HTTP endpoints ----------
@app.get("/")
async def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/audio/{key}")
async def audio(key: str):
    # Ưu tiên TTS WAV
    extless = key.replace(".wav", "").replace(".mp3", "")
    tts_path = os.path.join(TTS_DIR, f"{extless}.wav")
    if os.path.isfile(tts_path):
        return FileResponse(tts_path, media_type="audio/wav")

    # Fallback: pre-cached MP3
    mp3_path = os.path.join(K.AUDIO_DIR, f"{extless}.mp3")
    if os.path.isfile(mp3_path):
        return FileResponse(mp3_path, media_type="audio/mpeg")

    return JSONResponse({"error": "not found", "key": key}, status_code=404)


@app.get("/health")
async def health():
    return {
        "ok": True,
        "tts": TTS_AVAILABLE,
        "tts_voice": os.environ.get("KOON_VOICE", "mai_linh"),
        "tts_model": "Kokoro-Vietnamese (ONNX CPU)",
        "llm": bool(llm),
    }


@app.post("/asr")
async def asr(req: Request):
    """Nhận audio (webm/wav/mp3 từ mic) → text tiếng Việt."""
    data = await req.body()
    if not data:
        return JSONResponse({"text": "", "error": "no audio"}, status_code=400)
    tmp = tempfile.NamedTemporaryFile(suffix=".webm", delete=False)
    tmp.write(data)
    tmp.close()
    try:
        text = await asyncio.to_thread(transcribe_path, tmp.name)
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass
    log.info("ASR -> '%s'", text)
    return {"text": text}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")