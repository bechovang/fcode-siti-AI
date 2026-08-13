"""Server trò Cầu Vồng (KOON) — FastAPI + WebSocket + Kokoro TTS.
- Kokoro Vietnamese TTS (ONNX CPU): sinh giọng nói động, không cần pre-cache.
- KOON nói tự nhiên, lễ phép, đúng ngữ cảnh với từng câu trả lời của trẻ.
- 7 thử thách, chấm đáp án LLM/fuzzy, operator controls.
- STT chạy ở browser (Web Speech API: Chrome=Google / Edge=Azure) — không cần model server.

Backlog:
  - Live2D KOON: frontend (pixi-live2d-display), sync lip-sync với audio.
"""
import os
import sys
import json
import asyncio
import logging
import tempfile
import uuid
import unicodedata

# Load .env (nếu có python-dotenv) — đảm bảo đọc OPENROUTER_API_KEY, KOON_VOICE,...
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    load_dotenv()
except ImportError:
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import koon_data as K

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
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

# ---------- judge + reply ----------
def _norm_match(s: str) -> str:
    """Chuẩn hoá để so khớp: lowercase + bỏ dấu tiếng Việt + bỏ hết khoảng trắng.
    VD: 'con sư tử' / 'Con SU Tu' / 'con sứ tủ' đều -> 'consutu'."""
    s = (s or "").lower().strip()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))   # bỏ dấu
    return "".join(s.split())                                   # bỏ khoảng trắng


# Các từ đếm/loại từ đứng TRƯỚC danh từ (con/trái/cái/loài/quả...) cho phép lướt qua,
# nhưng PHẦN CÒN LẠI phải khớp chính xác đáp án -> không sinh false-positive.
def _answer_cores(t: str) -> set:
    """Từ input (đã chuẩn hoá, không dấu/không trắng), sinh các ứng viên "lõi đáp án":
    bỏ hết từ đếm/loại từ đứng trước (con/trái/cái/loài/quả/bông/ông/bà/em...) và
    bỏ 'con' đuôi (sư tử con). VD 'consutu'->{'consutu','sutu'}; 'duahay'->{'duahay'}."""
    ARTICLES = ("con", "cai", "trai", "qua", "loai", "bong", "ong", "ba", "em", "be", "chu", "co", "anh", "chi", "cu")
    cores = {t}
    for a in ARTICLES:
        if t.startswith(a):
            cores.add(t[len(a):])
    if t.endswith("con"):            # 'sư tử con' = sư tử non, vẫn là sư tử
        cores.add(t[:-3])
    cores.discard("")
    return cores


def judge_fuzzy(text: str, ch: dict) -> bool:
    """So khớp đáp án CHẶT — KHÔNG dùng fuzzy nữa.
    Chỉ ĐÚNG khi "lõi" của input (bỏ dấu, bỏ khoảng trắng, lướt từ đếm) KHỚP CHÍNH XÁC
    một đáp án/alias đầy đủ. Mọi thứ khác trả SAI (để LLM xử lý đáp án thay thế hợp lý).
    Bỏ partial_ratio/ratio (containment) trước đây sinh false-positive: 'con gà'=sư tử,
    'con chó'=sư tử, 'dua hay'=dưa hấu (vì 'dua' là alias 3 ký tự nằm lọt trong chuỗi)."""
    t = _norm_match(text)
    if not t:
        return False
    ncs = set(_norm_match(c) for c in [ch["answer"]] + ch.get("aliases", []))
    ncs.discard("")
    return bool(ncs.intersection(_answer_cores(t)))


def _reply_template(ch: dict, attempts: int) -> str:
    """Phản hồi fallback khi SAI (không có LLM hoặc LLM lỗi)."""
    hint = ch["hint"]
    if attempts <= 0:
        return f"Chưa đúng rồi các bạn ơi! Để mình gợi ý nha: {hint}. Các bạn thử lại xem?"
    return f"Gần được rồi! {hint}. Các bạn nghĩ thêm một chút nha, mình tin các bạn làm được!"


def _leaks_answer(reply: str, ch: dict) -> bool:
    """True nếu reply nhắc đến đáp án/alias (sau khi bỏ dấu + khoảng trắng).
    Dùng làm backstop: LLM đôi khi vẫn lỡ mồm dù prompt cấm → vứt reply đó."""
    def norm(s: str) -> str:
        s = (s or "").lower()
        s = unicodedata.normalize("NFKD", s)
        s = "".join(c for c in s if not unicodedata.combining(c))   # bỏ dấu
        return "".join(s.split())                                   # bỏ khoảng trắng
    nr = norm(reply)
    for cand in [ch["answer"]] + ch.get("aliases", []):
        nc = norm(cand)
        if len(nc) >= 4 and nc in nr:   # >=4 để tránh alias ngắn (dưa/sên/hè) false-positive
            return True
    return False


def judge_and_reply(text: str, ch: dict, attempts: int = 0):
    """Trả (correct, reply).
    - correct=True → reply='' (dùng pre-cache right, nhanh).
    - correct=False → reply là câu hội thoại (LLM động, hoặc template fallback).
    - correct=True, reply='' → đáp án dự định (dùng pre-cache right cho nhanh).
    - correct=True, reply≠'' → đáp án thay thế hợp lý, KOON xác nhận động.
    """
    # Fuzzy TRƯỚC: tin alias cho biến thể đã biết (không dấu, sai chính tả) —
    # chống LLM chấm sai những câu gần đúng rõ ràng (vd "qua dua ho" = dưa hấu).
    if judge_fuzzy(text, ch):
        return True, ""
    if llm:
        sysp = (
            "Bạn là KOON, nhân vật AI dẫn trò chơi đố vui cho trẻ em tiếng Việt. Nhiệm vụ:\n"
            "1. Chấm xem câu bé nói có THỎA MÃN mô tả câu đố không. Câu đố có thể có nhiều đáp án hợp lý — "
            "bất kỳ đáp án nào đúng với mô tả đều ĐÚNG. Ví dụ \"cái gì có 4 chân nhưng không biết đi\" thì "
            "\"cái bàn\", \"ghế\", \"tủ\", \"giường\" đều ĐÚNG. Đáp án không thỏa mãn mô tả mới là SAI. "
            "Chấp nhận sai chính tả, không dấu, từ đồng nghĩa, từ lễ phép (dạ/ạ/em). "
            "Một đáp án chỉ ĐÚNG khi RÕ RÀNG thỏa mãn TOÀN BỘ các đặc điểm trong mô tả; nếu chỉ hơi giống "
            "hoặc thiếu một đặc điểm quan trọng thì SAI.\n"
            "2. Nếu ĐÚNG: sinh 1-2 câu khen ngợi + xác nhận đáp án bé nói (chỉ dựa vào đặc điểm đã CÓ SẴN trong "
            "câu đố, không bịa). Ví dụ bé nói \"ghế\": \"Đúng rồi! Ghế cũng có bốn chân và không biết đi! Các bạn giỏi quá!\".\n"
            "3. Nếu SAI: sinh 1-2 câu đáp lại lễ phép, khích lệ thử lại. QUAN TRỌNG: BẮT BUỘC nhắc lại TRỌN VẸN nội dung "
            "Gợi ý đã cho (lấy nguyên 'Gợi ý' trong phần câu hỏi) để các đội có thêm thông tin đoán tiếp. TUYỆT ĐỐI KHÔNG "
            "chỉ nói chung chung kiểu 'nghe gợi ý rồi thử lại' mà không đưa ra nội dung gợi ý. QUY TẮC BẮT BUỘC (tránh "
            "lộ đáp án cho các đội khác):\n"
            "   - CHỈ được dùng thông tin từ câu bé nói và Gợi ý đã cho.\n"
            "   - TUYỆT ĐỐI KHÔNG nhắc tên, không mô tả, không ví dụ, không so sánh với đáp án đúng (kể cả khi bé đoán rất gần).\n"
            "   - KHÔNG đưa thêm đặc điểm MỚI của đáp án đúng (đặc điểm nào chưa có trong câu đố/gợi ý thì cấm nhắc tới).\n"
            "   Ví dụ bé nói \"cà chua\" (sai), gợi ý là \"đó là một loại trái cây mùa hè, vỏ xanh ruột đỏ, căng mọng "
            "nước\": chỉ nói kiểu \"Cà chua là một trái hay ghê, nhưng chưa phải đáp án mình tìm đâu! Gợi ý cho các "
            "bạn nè: đó là một loại trái cây mùa hè, vỏ xanh ruột đỏ, căng mọng nước. Các bạn thử lại nha!\" — được "
            "nhắc lại đúng Gợi ý nhưng KHÔNG được nhắc 'hạt đen', 'dưa' hay bất kỳ đặc điểm nào của đáp án đúng ngoài Gợi ý.\n"
            "Không bịa lý do sai sự thật để bác bỏ. Nếu không chắc đúng/sai, cho là SAI rồi gợi ý thêm.\n"
            "Luôn an toàn, vui vẻ, phù hợp trẻ em; không thô tục, không nhắc chuyện người lớn.\n"
            'Chỉ trả JSON hợp lệ: {"correct": true|false, "reply": "..."}.'
        )
        # KHÔNG đưa đáp án vào prompt — tránh LLM lỡ mồm nhắc tên đáp án trong phản hồi SAI.
        usrp = (f"Câu đố: \"{ch['question_text']}\". "
                f"Gợi ý (được phép dùng trong phản hồi): \"{ch['hint']}\". "
                f"Số lần bé đã sai trước đó: {attempts}. Câu bé vừa nói: \"{text}\".")
        try:
            r = llm.chat.completions.create(
                model=OR_MODEL,
                messages=[{"role": "system", "content": sysp}, {"role": "user", "content": usrp}],
                temperature=0.3,
            )
            data = json.loads(r.choices[0].message.content.strip())
            correct = bool(data.get("correct"))
            reply = (data.get("reply") or "").strip()
            if correct:
                return True, reply or "Đúng rồi! Các bạn giỏi quá!"
            reply = reply or _reply_template(ch, attempts)
            if _leaks_answer(reply, ch):
                # Backstop: LLM vẫn lỡ nhắc đáp án dù prompt cấm → vứt reply, dùng template an toàn.
                log.info("LLM reply lộ đáp án -> bỏ reply, dùng template an toàn")
                reply = _reply_template(ch, attempts)
            # Đảm bảo gợi ý LUÔN được nhắc lại dù LLM quên (đề phòng LLM chỉ nói 'nghe gợi ý rồi thử lại').
            if ch["hint"].lower() not in reply.lower():
                log.info("LLM reply thiếu gợi ý -> nối thêm gợi ý")
                reply = f"{reply} Gợi ý cho các bạn nè: {ch['hint']}."
            return False, reply
        except Exception as e:
            log.warning("LLM judge_and_reply lỗi (%s) -> template", e)

    # Fuzzy đã check ở đầu → đến đây chắc chắn SAI
    return False, _reply_template(ch, attempts)


# ---------- STT ----------
# Nhận diện giọng nói chạy ở BROWSER qua Web Speech API (Chrome=Google / Edge=Azure).
# Không cần model hay endpoint server → không download, khởi động nhẹ, trễ thấp.
log.info("STT: browser Web Speech API (Chrome=Google / Edge=Azure)")


# ---------- app ----------
app = FastAPI()
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Live2D models: serve từ ref/Open-LLM-VTuber (gitignored — KHÔNG commit asset proprietary)
LIVE2D_DIR = os.path.normpath(os.path.join(APP_DIR, "..", "ref", "Open-LLM-VTuber", "live2d-models"))
LIVE2D_AVAILABLE = os.path.isdir(LIVE2D_DIR)
if LIVE2D_AVAILABLE:
    app.mount("/live2d", StaticFiles(directory=LIVE2D_DIR), name="live2d")
    log.info("Live2D: /live2d (mao_pro) — từ ref/Open-LLM-VTuber/live2d-models")
else:
    log.warning("Live2D: thiếu ref/Open-LLM-VTuber/live2d-models — avatar dùng fallback emoji 🦊")

# Recap video: serve từ app/assets/video (tạo dir khi có file recap.mp4)
VIDEO_AVAILABLE = os.path.isdir(K.VIDEO_DIR)
if VIDEO_AVAILABLE:
    app.mount("/video", StaticFiles(directory=K.VIDEO_DIR), name="video")
    _mp4s = [f for f in os.listdir(K.VIDEO_DIR) if f.lower().endswith(".mp4")] if os.path.isdir(K.VIDEO_DIR) else []
    log.info("Video recap: /video — mp4: %s", _mp4s or "(chưa có → overlay fallback)")
else:
    log.info("Video recap: chưa có app/assets/video → overlay fallback")


def find_recap_video():
    """Tìm video recap: ưu tiên recap.mp4, không thì lấy .mp4 đầu tiên (alphabet).
    Trả (path, url) hoặc (None, None)."""
    if os.path.isfile(K.RECAP_VIDEO):
        return K.RECAP_VIDEO, "/video/recap.mp4"
    if os.path.isdir(K.VIDEO_DIR):
        for f in sorted(os.listdir(K.VIDEO_DIR)):
            if f.lower().endswith(".mp4") and os.path.isfile(os.path.join(K.VIDEO_DIR, f)):
                return os.path.join(K.VIDEO_DIR, f), f"/video/{f}"
    return None, None


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
        self._video_done = asyncio.Event()
        self._continue_ready = asyncio.Event()  # chờ operator bấm nút "nói tiếp" trong intro
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

    async def play_or_say(self, key: str, fallback_text: str = ""):
        """Phát pre-cache (.wav) nếu có → tức thì; không thì Kokoro động (chịu lỗi)."""
        wav = os.path.join(K.AUDIO_DIR, f"{key}.wav")
        if os.path.isfile(wav):
            await self.play(key)
        elif fallback_text:
            await self.say(fallback_text)
        else:
            log.warning("play_or_say: thiếu %s.wav và không có fallback", key)

    def interrupt(self):
        """Ngắt mọi điểm chờ block (audio/answer/video) để operator op
        (skip/replay/force_correct) được xử lý ngay thay vì kẹt trong await wait()."""
        self._audio_done.set()
        self._answer_ready.set()
        self._video_done.set()
        self._continue_ready.set()

    async def state(self):
        await self.send({
            "type": "state",
            "phase": self.phase,
            "idx": self.idx,
            "unlocked": self.unlocked,
            "total": len(K.CHALLENGES),
        })


# ---------- kịch bản KOON với TTS động ----------
# Intro tương tác: KOON nói từng đoạn bằng file pre-cache (phát TỨC THÌ, không synth động).
# Mỗi đoạn = 1 hoặc nhiều file .wav đã gen sẵn trong app/assets/audio/koon/.
# Muốn đổi lời thoại? Sửa trong app/scripts/gen_koon_voice.py (LINES) rồi chạy lại lệnh gen.
INTRO_CHUNK_KEYS = [
    ["01_intro_greet", "02_intro_rainbow_q"],   # đoạn 1: chào + "thích ngắm cầu vồng không?"
    ["03_intro_lost_colors"],                    # đoạn 2: "giúp KOON tìm 7 sắc màu... không?"
    ["04_intro_rule"],                           # đoạn 3: "sẵn sàng đồng hành... chưa?"
    ["05_intro_start"],                          # đoạn 4: "chuyến phiêu lưu bắt đầu thôi!"
]
# Chữ hiện trên nút "nói tiếp" ở góc trái trên (câu operator cần chờ trẻ đồng thanh).
INTRO_PROMPTS = ["👏 Có!", "👏 Có!", "👏 Sẵn sàng!", "👏 Bắt đầu!"]

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


async def run_flow(s: Session):
    """Chạy kịch bản 7 thử thách với TTS động."""
    try:
        # ---- INTRO (tương tác: KOON nói từng đoạn, dừng sau mỗi đoạn chờ operator bấm nút) ----
        s.phase = "intro"
        await s.state()
        for i, keys in enumerate(INTRO_CHUNK_KEYS):
            if s._op == "skip":
                s._op = None
                break
            for key in keys:
                await s.play_or_say(key, "")   # pre-cache .wav → phát tức thì (không synth động)
            if s._op == "skip":
                s._op = None
                break
            s._continue_ready.clear()
            await s.send({"type": "intro_pause", "prompt": INTRO_PROMPTS[i]})
            await s._continue_ready.wait()

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

            attempts = 0
            read_q = True  # đọc câu hỏi lần đầu (và mỗi khi operator bấm replay)
            while True:  # vòng lặp thử lại khi sai
                if s._op == "skip":
                    s._op = None
                    break

                # KOON đọc câu hỏi (chỉ lần đầu hoặc khi replay — KHÔNG lặp lại khi sai)
                if read_q or s._op == "replay":
                    if s._op == "replay":
                        s._op = None
                    await s.play_or_say(
                        ch["q"],
                        f"Câu hỏi thứ {ch['n']} màu {ch['color'].lower()}: {ch['question_text']}",
                    )
                    read_q = False
                    if s._op == "skip":
                        s._op = None
                        break

                # Chờ trẻ trả lời
                s.phase = "await"
                await s.state()
                await s.send({"type": "await_answer"})
                s._answer_ready.clear()
                s._answer = None
                if s._op in ("force_correct", "skip"):
                    # op đã bấm trước khi vào await → thoát wait ngay
                    s._answer_ready.set()
                await s._answer_ready.wait()

                if s._op == "skip":
                    s._op = None
                    break

                ans = s._answer or ""
                if s._op == "force_correct":
                    s._op = None
                    correct = True
                    reply = ""
                else:
                    correct, reply = judge_and_reply(ans, ch, attempts)
                attempts += 1

                log.info("Thử thách %d (lần %d): '%s' -> %s", ch["n"], attempts, ans, "ĐÚNG" if correct else "SAI")
                s.phase = "feedback"
                await s.state()

                if correct:
                    # Phản hồi ĐÚNG ngay (confetti + chime ở frontend) TRƯỚC khi KOON nói
                    await s.send({"type": "correct_answer", "hex": ch["hex"]})
                    await asyncio.sleep(0.6)  # chờ chime đúng phát xong rồi KOON mới nói
                    if reply:
                        # Đáp án thay thế hợp lý → LLM reply động xác nhận (đúng sự thật)
                        await s.say(reply)
                    else:
                        # Đáp án dự định → pre-cache right (nhanh)
                        await s.play_or_say(
                            ch["right"],
                            f"Chính xác! Đáp án là {ch['answer']}. Các bạn giỏi quá! Mảnh màu {ch['color'].lower()} đã được tìm thấy!",
                        )
                    s.unlocked.append(ch["hex"])
                    await s.send({"type": "unlock_color", "hex": ch["hex"]})
                    break
                else:
                    # Phản hồi hội thoại động (LLM/Kokoro) — KHÔNG đọc lại câu hỏi
                    # Tiếng báo sai phát trước, đợi ~0.6s rồi KOON mới nói (không đè tiếng)
                    await s.send({"type": "wrong_answer"})
                    await asyncio.sleep(0.6)
                    await s.say(reply)

        # ---- RAINBOW ----
        s.phase = "rainbow"
        await s.state()
        await s.send({"type": "rainbow"})
        await asyncio.sleep(4)

        # ---- RECAP ----
        s.phase = "recap"
        await s.state()
        await s.play_or_say(K.RECAP, OUTRO_RECAP)
        # Magic reveal: KOON bay giữa màn + hô biến → chuyển video
        await s.send({"type": "magic_reveal"})
        await s.say(MAGIC_LINE)
        await asyncio.sleep(0.3)
        # Phát video recap nếu có file mp4; không thì overlay animation fallback.
        s._video_done.clear()
        _vpath, vurl = find_recap_video()
        if vurl:
            log.info("Recap video phát: %s", vurl)
            await s.send({"type": "play_video", "url": vurl})
        else:
            await s.send({"type": "show_recap_overlay"})
        await s._video_done.wait()

        # ---- DONE ----
        s.phase = "done"
        await s.state()
        await s.play_or_say(K.GOODBYE, OUTRO_GOODBYE)
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
            elif t == "continue":
                s._continue_ready.set()
            elif t in ("video_ended", "overlay_ended"):
                s._video_done.set()
            elif t == "answer":
                s._answer = msg.get("text", "")
                log.info("Answer [%s]: '%s'", msg.get("stt") or "typed", s._answer)
                s._answer_ready.set()
            elif t == "op":
                a = msg.get("action")
                if a == "restart":
                    await start()
                elif a == "force_correct":
                    s._op = "force_correct"
                    s.interrupt()  # giải phóng await_answer → check force_correct
                elif a == "skip":
                    s._op = "skip"
                    await s.send({"type": "stop_audio"})  # dừng audio đang phát
                    s.interrupt()
                elif a == "replay":
                    s._op = "replay"
                    await s.send({"type": "stop_audio"})
                    s.interrupt()
    except WebSocketDisconnect:
        log.info("WS ngắt")
        if s.flow_task:
            s.flow_task.cancel()


# ---------- HTTP endpoints ----------
@app.get("/")
async def index():
    # no-store: browser luôn tải index.html mới (tránh chạy bản cũ khi đã sửa frontend)
    return FileResponse(os.path.join(STATIC_DIR, "index.html"), headers={"Cache-Control": "no-store"})


@app.get("/audio/{key}")
async def audio(key: str):
    extless = key.replace(".wav", "").replace(".mp3", "")
    # no-store: browser LUÔN lấy file mới (tránh chơi audio cũ sau khi regen .wav)
    NO_CACHE = {"Cache-Control": "no-store"}
    # 1. TTS động (Kokoro say()) — temp WAV
    tts_path = os.path.join(TTS_DIR, f"{extless}.wav")
    if os.path.isfile(tts_path):
        return FileResponse(tts_path, media_type="audio/wav", headers=NO_CACHE)
    # 2. Pre-cache Kokoro — .wav trong AUDIO_DIR
    wav_path = os.path.join(K.AUDIO_DIR, f"{extless}.wav")
    if os.path.isfile(wav_path):
        return FileResponse(wav_path, media_type="audio/wav", headers=NO_CACHE)
    # 3. Backup edge-tts — .mp3 trong AUDIO_DIR
    mp3_path = os.path.join(K.AUDIO_DIR, f"{extless}.mp3")
    if os.path.isfile(mp3_path):
        return FileResponse(mp3_path, media_type="audio/mpeg", headers=NO_CACHE)

    return JSONResponse({"error": "not found", "key": key}, status_code=404)


@app.get("/health")
async def health():
    return {
        "ok": True,
        "tts": TTS_AVAILABLE,
        "tts_voice": os.environ.get("KOON_VOICE", "mai_linh"),
        "tts_model": "Kokoro-Vietnamese (ONNX CPU)",
        "stt": "browser (Web Speech API)",
        "llm": bool(llm),
        "llm_model": OR_MODEL if llm else None,
        "live2d": LIVE2D_AVAILABLE,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")