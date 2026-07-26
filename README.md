# F-Code SITI AI — Summer 2026 Gala

Dự án xây dựng phần mềm AI cho phần giao lưu/giải trí trên sân khấu Gala LHTT **Summer 2026 (SUM26)** tại **Trung tâm Phát huy Bình Thọ**.

Đội ngũ thực hiện: **F-Code**

---

## Trò chơi

### 1. Cùng Koon Đi Tìm Cầu Vồng (AI hội thoại) ✅ Đang triển khai

Trẻ đồng hành cùng nhân vật AI **KOON** vượt qua **7 thử thách** để tìm lại 7 sắc màu cầu vồng.

- **Cách chơi**: KOON đọc câu đố → trẻ trả lời (micro hoặc gõ chữ) → LLM chấm đúng/sai → đúng: mở khóa mảnh màu, sai: KOON gợi ý → thử lại
- **Công nghệ**: Kokoro Vietnamese TTS (ONNX CPU) → OpenRouter LLM (GPT-4o-mini) → STT Web Speech API (Chrome=Google / Edge=Azure) → Live2D avatar (mao_pro, lip-sync theo giọng TTS)
- **Thời lượng**: ~10–11 phút
- **Server**: FastAPI + WebSocket (`app/server.py`)

### 2. Tìm Nắng Cùng AI (nhận diện hình ảnh) ⏳ Kế hoạch

Trò đối kháng đồng đội. Trẻ bốc đồ mù trong thùng → giơ trước camera → AI nhận diện → về đích. Tính điểm 3-2-1.

- **Công nghệ**: Object recognition + bảng điểm real-time
- **Thời lượng**: ~5 phút

---

## 🚀 Hướng dẫn chạy (Step-by-Step)

### Yêu cầu

| Thành phần | Yêu cầu |
|---|---|
| **Python** | ≥ 3.10 |
| **Trình duyệt** | **Chrome hoặc Edge** (cần Web Speech API cho mic) |
| **Mạng** | Cần internet (STT gửi audio lên Google/Azure) |
| **RAM** | ≥ 4GB (khuyến nghị 8GB+) |
| **CPU** | Đa lõi (TTS chạy ONNX CPU, ~5x realtime) |
| **Ổ cứng** | ~2GB trống (cho model TTS Kokoro) |
| **HĐH** | Windows (có thể chạy Linux/macOS) |

### Bước 1: Clone repo

```bash
git clone https://github.com/bechovang/fcode-siti-AI.git
cd fcode-siti-AI
```

### Bước 2: Cập nhật submodules

```bash
git submodule update --init --recursive
```

Lệnh này clone **Kokoro-Vietnamese** (TTS) — model ~2GB sẽ được download tự động khi chạy lần đầu.

### Bước 3: Tạo virtual environment

**Windows (cmd hoặc PowerShell):**
```cmd
python -m venv .venv
.venv\Scripts\activate
```

**Linux/macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Bước 4: Cài Kokoro Vietnamese TTS (ONNX)

```bash
pip install -e "ref/Kokoro-Vietnamese[onnx]"
```

> ⏱ Lần đầu cài có thể mất 5-10 phút (download torch, transformers, onnxruntime).

### Bước 5: Cài các dependencies còn lại

```bash
pip install fastapi uvicorn openai rapidfuzz soundfile
```

### Bước 6: Thiết lập API keys

**Cần thiết** (nếu không có, LLM judge sẽ fallback về fuzzy match kém chính xác hơn):

```cmd
set OPENROUTER_API_KEY=sk-or-v1-...   # Windows
```

```bash
export OPENROUTER_API_KEY=sk-or-v1-...   # Linux/macOS
```

👉 Đăng ký key miễn phí tại [OpenRouter.ai](https://openrouter.ai/)

### Bước 7: Chạy server

```bash
python app/server.py
```

Bạn sẽ thấy log:

```
INFO TTS temp dir: C:\Users\...\koon_tts_xxx
INFO LLM judge: OpenRouter openai/gpt-4o-mini
INFO Kokoro TTS sẵn sàng (giọng mai_linh, device=cpu)
INFO STT: browser Web Speech API (Chrome=Google / Edge=Azure)
INFO Uvicorn running on http://0.0.0.0:8000
```

### Bước 8: Mở trình duyệt (Chrome hoặc Edge)

Vào **http://localhost:8000** bằng **Chrome/Edge** (cần Web Speech API cho mic).

- Bấm **"🧪 Test mic / STT"** để kiểm tra nhận diện giọng nói trước khi chơi.
- Bấm **"Bắt đầu"** → KOON sẽ nói chuyện và đặt câu hỏi!

> ⚠️ STT cần **internet** (audio gửi lên Google/Azure). Nếu truy cập bằng IP thay vì `localhost` (vd `http://192.168.x.x:8000`) thì phải dùng **HTTPS**, nếu không browser sẽ chặn mic.

---

## ⚙️ Tuỳ chỉnh

### Đổi giọng KOON

Kokoro có 14 giọng tiếng Việt:

| Giọng | Mô tả |
|---|---|
| `mai_linh` | 🥇 Nữ, dễ thương — **mặc định** |
| `diem_trinh` | Nữ, nhẹ nhàng |
| `thuc_trinh` | Nữ, tự nhiên |
| `ngoc_huyen` | Nữ, trẻ trung |
| `my_yen` | Nữ, ấm áp |
| `mai_loan` | Nữ, chậm rãi |
| `phat_tai` | Nam, vui vẻ |
| `hung_thinh` | Nam |
| `manh_dung` | Nam |
| `thanh_dat` | Nam |
| `tuan_ngoc` | Nam |
| `duc_an` | Nam |
| `duc_duy` | Nam |
| `storyvert` | Giọng kể chuyện |

```cmd
set KOON_VOICE=diem_trinh
python app/server.py
```

### Đổi model LLM

```cmd
set OR_MODEL=anthropic/claude-sonnet-4
set OR_MODEL=google/gemini-2.0-flash-001
```

### Toàn bộ biến môi trường

| Biến | Mặc định | Bắt buộc | Mô tả |
|---|---|---|---|
| `KOON_VOICE` | `mai_linh` | ❌ | Giọng TTS (14 giọng VN) |
| `OPENROUTER_API_KEY` | - | ⚠️ Nên có | API key cho LLM judge |
| `OR_MODEL` | `openai/gpt-4o-mini` | ❌ | Model LLM trên OpenRouter |

---

## 🌐 API Endpoints

| Endpoint | Method | Mô tả |
|---|---|---|
| `/` | GET | Trang chủ (giao diện game) |
| `/ws` | WebSocket | Kết nối game real-time |
| `/audio/{key}` | GET | Lấy file audio (WAV từ TTS hoặc MP3 cached) |
| `/health` | GET | Kiểm tra trạng thái server (TTS/LLM/STT) |

### WebSocket Messages

**Server → Client:**
```json
{"type": "play_audio", "key": "tts_abc123", "tts": true}
{"type": "state", "phase": "ask", "idx": 0, "unlocked": [], "total": 7}
{"type": "show_question", "text": "...", "color": "Đỏ", "hex": "#e74c3c"}
{"type": "await_answer"}
{"type": "unlock_color", "hex": "#e74c3c"}
{"type": "rainbow"}
{"type": "ready"}
{"type": "reset"}
```

**Client → Server:**
```json
{"type": "start"}
{"type": "audio_ended"}
{"type": "answer", "text": "dưa hấu", "stt": "web-speech"}   // "stt": "web-speech" (mic) hoặc bỏ trống (gõ tay)
{"type": "op", "action": "skip"}
```

---

## 🏗 Cấu trúc thư mục

```
├── app/                        # Ứng dụng Python chính
│   ├── server.py               # 🎯 Server FastAPI + WebSocket + Kokoro TTS
│   ├── koon_data.py            # 📦 Dữ liệu 7 câu hỏi + đáp án + gợi ý
│   ├── scripts/                # Scripts phụ trợ
│   │   ├── gen_koon_voice.py       # Tạo voice mẫu (legacy)
│   │   └── gen_koon_voice_capcut.py
│   └── static/
│       ├── index.html          # 🖥 Giao diện game + Live2D KOON (lip-sync theo giọng TTS)
│       └── libs/               # 🧩 pixi v6 + Cubism core + pixi-live2d-display (vendor local)
├── docs/                       # Tài liệu dự án
│   ├── source-brief.md         # Tổng hợp yêu cầu
│   └── kich-ban-koon.md        # Kịch bản chi tiết
├── ref/                        # Reference implementations
│   ├── Kokoro-Vietnamese/      # ✅ TTS tiếng Việt (ONNX, 14 giọng)
│   ├── Open-LLM-VTuber/        # 🦊 Nguồn model Live2D (mao_pro) — gitignore, không commit
│   ├── pipecat/                # ⏸️ Real-time voice pipeline (future)
│   └── ...                     # Các reference khác
├── thongtin/                   # Tài liệu gốc (.docx)
├── .gitignore
├── .gitmodules
└── README.md
```

---

## Kiến trúc hệ thống

### Pipeline xử lý

```
┌──────────────────────────┐        ┌──────────────────────────────┐
│ Client (Chrome / Edge)   │  WS    │ FastAPI Server                │
│                          │◄──────►│                              │
│ 🎤 Mic → Web Speech API  │ text   │  Session Flow (7 thử thách)   │
│   nhận diện tiếng Việt   │───────►│      │                       │
│                          │        │      ├─► LLM Judge (Đ/S)      │
│ 🔊 <audio> phát TTS      │        │      │   (OpenRouter / Fuzzy) │
│   từ /audio/{key}        │◄───────│      └─► Kokoro TTS → WAV     │
└──────────────────────────┘ audio  │           (ONNX CPU)          │
                                    └──────────────────────────────┘
```

### TTS Performance

| Độ dài câu | Thời gian gen | Hệ số |
|---|---|---|
| 3 giây nói | ~0.55 giây | 5.4x realtime |
| 10 giây nói | ~2 giây | 5x realtime |

---

## 🔧 Troubleshooting

### "Kokoro Vietnamese chưa cài" khi chạy server

```bash
pip install -e "ref/Kokoro-Vietnamese[onnx]"
```

### Lỗi port 8000 đã được dùng

```bash
# Windows: tìm và kill process đang giữ port
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Ko có OpenRouter key — server vẫn chạy được không?

Có. Server sẽ dùng **fuzzy match** (so khớp chữ cái) để chấm đáp án. Kém chính xác hơn LLM nhưng vẫn hoạt động.

### Mic / STT không nhận giọng nói

- Dùng **Chrome hoặc Edge** (Firefox/Safari có thể không hỗ trợ Web Speech API).
- Cấp quyền mic cho site (icon khoá/mic góc trình duyệt).
- Cần **internet** (STT gửi audio lên Google/Azure).
- Nếu truy cập bằng IP thay vì `localhost` → phải dùng **HTTPS** (browser chỉ cho phép mic trên localhost hoặc HTTPS).
- Bấm **"🧪 Test mic / STT"** ở màn start để kiểm tra nhanh — kết quả hiện kèm engine đang dùng.
- Trên sân khấu nếu STT vẫn nhận sai: operator bấm **F (Ép đúng)** để KOON tiếp tục.

### KOON vẫn là emoji 🦊 (Live2D không hiện)

Avatar Live2D lấy từ `ref/Open-LLM-VTuber/live2d-models/` (thư mục này **gitignore** — không có sau fresh clone). Nếu thiếu, game tự **fallback về emoji 🦊**, vẫn chơi bình thường. Để có avatar:

```bash
git clone https://github.com/Open-LLM-VTuber/Open-LLM-VTuber.git ref/Open-LLM-VTuber
```

Restart server → log hiện `Live2D: /live2d (mao_pro)` và `/health` trả `"live2d": true`. (Model mao_pro = Niziiro Mao, sample Live2D free-material.)

### Giọng đọc bị "robot" / không tự nhiên

Thử đổi giọng:
```cmd
set KOON_VOICE=thuc_trinh
```

Hoặc dùng `storyvert` (giọng kể chuyện, chậm hơn nhưng cảm xúc hơn).

---

## 📚 Tham khảo

- [Kokoro Vietnamese](https://github.com/iamdinhthuan/Kokoro-Vietnamese) — TTS tiếng Việt ONNX CPU
- [Web Speech API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API) — STT trong browser (Chrome=Google / Edge=Azure)
- [Pipecat](https://github.com/pipecat-ai/pipecat) — Real-time voice pipeline framework (future consideration)
- [OpenRouter](https://openrouter.ai/) — Unified LLM API