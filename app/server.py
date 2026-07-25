"""Server trò Cầu Vồng (KOON) — FastAPI + WebSocket.
Backbone: chạy kịch bản 7 thử thách, phát audio pre-cache, chấm đáp án (LLM/fuzzy),
operator controls (skip/force_correct/replay/restart).

Cắm thêm ở các hook:
  - STT (PhoWhisper): frontend stream audio -> endpoint transcribe() (xem /asr).
  - Live2D KOON: frontend (pixi-live2d-display), sync lip-sync với audio đang phát.
  - Khử ồn DSP: tiền xử lý audio trước khi vào STT.
"""
import os
import sys
import json
import asyncio
import logging
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import koon_data as K

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from rapidfuzz import fuzz

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("koon")

APP_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(APP_DIR, "static")

OR_KEY = os.environ.get("OPENROUTER_API_KEY", "").strip()
OR_BASE = "https://openrouter.ai/api/v1"
OR_MODEL = os.environ.get("OR_MODEL", "openai/gpt-4o-mini")
llm = OpenAI(base_url=OR_BASE, api_key=OR_KEY) if OR_KEY else None
log.info("LLM judge: %s", "OpenRouter " + OR_MODEL if llm else "TẮT — dùng fuzzy match")

app = FastAPI()
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


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
        mname = os.environ.get("WHISPER_MODEL", "diepho/PhoWhisper-small-ct2")  # PhoWhisper (CT2)
        log.info("Load Whisper '%s' (CPU int8) — ~20s lần đầu...", mname)
        _whisper = WhisperModel(mname, device="cpu", compute_type="int8")
        log.info("Whisper sẵn sàng.")
    return _whisper


def transcribe_path(path: str) -> str:
    m = get_whisper()
    # initial_prompt: neo giải mã về TIẾNG VIỆT + từ vựng đáp án → chống hallucination tiếng Anh
    # ("your house"...) khi audio mic yếu/ồn.
    vocab = ", ".join(ch["answer"] for ch in K.CHALLENGES)
    prompt = f"Trò chơi đố vui cho trẻ em tiếng Việt. Một số từ thường gặp: {vocab}."
    segs, _ = m.transcribe(
        path,
        language="vi",
        beam_size=1,
        vad_filter=True,
        initial_prompt=prompt,
        condition_on_previous_text=False,  # không để hallucination lan truyền
        no_speech_threshold=0.6,
    )
    return " ".join(s.text for s in segs).strip()


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

    async def send(self, msg: dict):
        await self.ws.send_text(json.dumps(msg, ensure_ascii=False))

    async def play(self, key: str):
        self._audio_done.clear()
        await self.send({"type": "play_audio", "key": key})
        await self._audio_done.wait()

    async def state(self):
        await self.send({"type": "state", "phase": self.phase, "idx": self.idx,
                         "unlocked": self.unlocked, "total": len(K.CHALLENGES)})


async def run_flow(s: Session):
    try:
        s.phase = "intro"; await s.state()
        for key in K.INTRO:
            if s._op == "skip":
                s._op = None; break
            await s.play(key)

        for i, ch in enumerate(K.CHALLENGES):
            s.idx = i
            s.phase = "ask"; await s.state()
            await s.send({"type": "show_question", "text": ch["question_text"],
                          "color": ch["color"], "hex": ch["hex"]})
            while True:  # vòng thử lại khi sai
                if s._op == "skip":
                    s._op = None
                    break
                await s.play(ch["q"])
                if s._op == "replay":
                    s._op = None
                    continue
                if s._op == "skip":
                    s._op = None
                    break
                s.phase = "await"; await s.state()
                await s.send({"type": "await_answer"})
                s._answer_ready.clear(); s._answer = None
                await s._answer_ready.wait()
                ans = s._answer or ""
                if s._op == "force_correct":
                    s._op = None; correct = True
                else:
                    correct = judge(ans, ch)
                log.info("Thử thách %d: '%s' -> %s", ch["n"], ans, "ĐÚNG" if correct else "SAI")
                s.phase = "feedback"; await s.state()
                if correct:
                    await s.play(ch["right"])
                    s.unlocked.append(ch["hex"])
                    await s.send({"type": "unlock_color", "hex": ch["hex"]})
                    break
                else:
                    await s.play(ch["wrong"])  # lặp lại: đọc lại gợi ý + hỏi lại

        s.phase = "rainbow"; await s.state()
        await s.send({"type": "rainbow"})
        await asyncio.sleep(4)
        s.phase = "recap"; await s.state()
        await s.play(K.RECAP)
        s.phase = "done"; await s.state()
        await s.play(K.GOODBYE)
        log.info("Hoàn thành show.")
    except asyncio.CancelledError:
        raise


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    s = Session(ws)

    async def start():
        if s.flow_task and not s.flow_task.done():
            s.flow_task.cancel()
        s.idx = 0; s.unlocked = []; s._op = None; s._answer = None
        await s.send({"type": "reset"})
        s.flow_task = asyncio.create_task(run_flow(s))

    await s.send({"type": "ready"})  # chờ frontend bấm "Bắt đầu" (mở khóa autoplay)
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


@app.get("/")
async def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/audio/{key}")
async def audio(key: str):
    if key.endswith(".mp3"):
        key = key[:-4]
    p = os.path.join(K.AUDIO_DIR, f"{key}.mp3")
    if not os.path.isfile(p):
        return JSONResponse({"error": "not found", "key": key}, status_code=404)
    return FileResponse(p, media_type="audio/mpeg")


@app.get("/health")
async def health():
    return {"ok": True, "llm": bool(llm), "audio_count": len(os.listdir(K.AUDIO_DIR))}


@app.post("/asr")
async def asr(req: Request):
    """Nhận audio (webm/wav/mp3 từ mic) → text tiếng Việt."""
    data = await req.body()
    if not data:
        return JSONResponse({"text": "", "error": "no audio"}, status_code=400)
    ext = ".webm"
    tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
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
