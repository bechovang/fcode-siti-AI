# F-Code SITI AI — Summer 2026 Gala

Dự án xây dựng phần mềm AI cho phần giao lưu/giải trí trên sân khấu Gala LHTT **Summer 2026 (SUM26)** tại **Trung tâm Phát huy Bình Thọ**.

Đội ngũ thực hiện: **F-Code**

---

## Trò chơi

### 1. Cùng Koon Đi Tìm Cầu Vồng (AI hội thoại) ✅ Đang triển khai

Trẻ đồng hành cùng nhân vật AI **KOON** vượt qua **7 thử thách** để tìm lại 7 sắc màu cầu vồng.

- **Cách chơi**: KOON đọc câu đố → trẻ trả lời (micro hoặc gõ chữ) → LLM chấm đúng/sai → đúng: mở khóa mảnh màu, sai: KOON gợi ý → thử lại
- **Công nghệ**: Kokoro Vietnamese TTS (ONNX CPU) → OpenRouter LLM (GPT-4o-mini) → ggml-PhoWhisper-small (whisper.cpp)
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
| **RAM** | ≥ 8GB (khuyến nghị 16GB+) |
| **CPU** | Đa lõi (TTS chạy ONNX CPU, ~5x realtime) |
| **Ổ cứng** | ~5GB trống (cho model TTS + Whisper) |
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

### Bước 5: Tải model ASR (ggml-PhoWhisper-small, 465MB)

```bash
mkdir -p app/models
python -c "
import requests
url = 'https://huggingface.co/dongxiat/ggml-PhoWhisper-small/resolve/b6677d19bc96a276d7cf5006e2ea18e18d02df16/ggml-PhoWhisper-small.bin'
with open('app/models/ggml-PhoWhisper-small.bin', 'wb') as f:
    resp = requests.get(url, stream=True, timeout=600)
    resp.raise_for_status()
    for chunk in resp.iter_content(8192): f.write(chunk)
print('OK')
"
```

### Bước 6: Cài các dependencies còn lại

```bash
pip install fastapi uvicorn openai rapidfuzz soundfile pywhispercpp
```

### Bước 7: Thiết lập API keys

**Cần thiết** (nếu không có, LLM judge sẽ fallback về fuzzy match kém chính xác hơn):

```cmd
set OPENROUTER_API_KEY=sk-or-v1-...   # Windows
```

```bash
export OPENROUTER_API_KEY=sk-or-v1-...   # Linux/macOS
```

👉 Đăng ký key miễn phí tại [OpenRouter.ai](https://openrouter.ai/)

### Bước 8: Chạy server

```bash
python app/server.py
```

Bạn sẽ thấy log:

```
INFO TTS temp dir: C:\Users\...\koon_tts_xxx
INFO LLM judge: OpenRouter openai/gpt-4o-mini
INFO Kokoro TTS sẵn sàng (giọng mai_linh, device=cpu)
INFO Uvicorn running on http://0.0.0.0:8000
```

### Bước 9: Mở trình duyệt

Vào **http://localhost:8000** → bấm **"Bắt đầu"** → KOON sẽ nói chuyện và đặt câu hỏi!

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
| `WHISPER_MODEL_PATH` | `app/models/ggml-PhoWhisper-small.bin` | ❌ | Path file model GGML ASR |

---

## 🌐 API Endpoints

| Endpoint | Method | Mô tả |
|---|---|---|
| `/` | GET | Trang chủ (giao diện game) |
| `/ws` | WebSocket | Kết nối game real-time |
| `/audio/{key}` | GET | Lấy file audio (WAV từ TTS hoặc MP3 cached) |
| `/asr` | POST | Nhận audio → trả text tiếng Việt |
| `/health` | GET | Kiểm tra trạng thái server |

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
{"type": "answer", "text": "dưa hấu"}
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
│       └── index.html          # 🖥 Giao diện game
├── docs/                       # Tài liệu dự án
│   ├── source-brief.md         # Tổng hợp yêu cầu
│   └── kich-ban-koon.md        # Kịch bản chi tiết
├── ref/                        # Reference implementations
│   ├── Kokoro-Vietnamese/      # ✅ TTS tiếng Việt (ONNX, 14 giọng)
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
                   ┌─────────────────────────────────────┐
                   │         FastAPI Server               │
                   │                                     │
  ┌──────┐  WS   ┌▼────────┐  text  ┌──────────┐  Đ/S  ┌────────┐
  │Client│◄─────►│Session  │◄──────►│LLM Judge │◄─────►│KOON    │
  │(Web) │       │Flow     │        │(OpenAI/  │       │Script  │
  └──────┘       └──┬──────┘        │ Fuzzy)   │       └───┬────┘
                    │               └──────────┘           │
                    │ audio                                │ text
               ┌────▼─────┐                         ┌──────▼─────┐
               │/audio    │                         │Kokoro TTS  │
               │endpoint  │                         │(ONNX CPU)  │
               └──────────┘                         └────────────┘
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

### "pywhispercpp" không cài

```bash
pip install pywhispercpp
```

### Giọng đọc bị "robot" / không tự nhiên

Thử đổi giọng:
```cmd
set KOON_VOICE=thuc_trinh
```

Hoặc dùng `storyvert` (giọng kể chuyện, chậm hơn nhưng cảm xúc hơn).

---

## 📚 Tham khảo

- [Kokoro Vietnamese](https://github.com/iamdinhthuan/Kokoro-Vietnamese) — TTS tiếng Việt ONNX CPU
- [Pipecat](https://github.com/pipecat-ai/pipecat) — Real-time voice pipeline framework (future consideration)
- [ggml-PhoWhisper-small](https://huggingface.co/dongxiat/ggml-PhoWhisper-small) — ASR tiếng Việt (whisper.cpp GGML)
- [OpenRouter](https://openrouter.ai/) — Unified LLM API