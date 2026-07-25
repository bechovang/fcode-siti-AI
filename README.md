# F-Code SITI AI — Summer 2026 Gala

Dự án xây dựng phần mềm AI cho phần giao lưu/giải trí trên sân khấu Gala LHTT **Summer 2026 (SUM26)** tại **Trung tâm Phát huy Bình Thọ**.

Đội ngũ thực hiện: **F-Code**

## Trò chơi

### 1. Cùng Koon Đi Tìm Cầu Vồng (AI hội thoại) ✅ Đang triển khai

Trẻ đồng hành cùng nhân vật AI **KOON** vượt qua **7 thử thách** để tìm lại 7 sắc màu cầu vồng. Mỗi thử thách là một câu đố. Trả lời đúng → AI mở khóa 1 mảnh màu. Hoàn thành → cầu vồng phát sáng → video recap.

- **Công nghệ**: Kokoro Vietnamese TTS (ONNX CPU) → OpenRouter LLM (GPT-4o-mini) → PhoWhisper STT
- **Thời lượng**: ~10–11 phút
- **Server**: FastAPI + WebSocket (`app/server.py`)

### 2. Tìm Nắng Cùng AI (nhận diện hình ảnh) ⏳ Kế hoạch

Trò đối kháng đồng đội. Trẻ bốc đồ mù trong thùng vật phẩm → giơ trước camera → AI nhận diện → đúng thì về đích. Tính điểm 3-2-1.

- **Công nghệ**: Object recognition (AI nhận diện hình ảnh) + bảng điểm real-time
- **Thời lượng**: ~5 phút

## Kiến trúc hệ thống

### Luồng xử lý Trò 1 (Cầu Vồng)

```
[KOON nói TTS] ──WebSocket──▶ [Frontend: phát WAV + hiệu ứng]
[Trẻ trả lời]  ────Mic─────▶ [/asr: PhoWhisper] ──text──▶ [LLM Judge]
[Judge] ──Đúng/Sai──▶ [KOON phản hồi động] ──TTS──▶ [Phát tiếp]
```

### Công nghệ hiện tại

| Thành phần | Công nghệ | Trạng thái |
|---|---|---|
| **TTS** | Kokoro Vietnamese (ONNX CPU, 14 giọng) | ✅ Đã tích hợp |
| **LLM Judge** | OpenRouter GPT-4o-mini (hoặc fuzzy fallback) | ✅ Đã tích hợp |
| **ASR** | faster-whisper / PhoWhisper (CPU int8) | ✅ Đã tích hợp |
| **Server** | FastAPI + WebSocket | ✅ Đã tích hợp |
| **Frontend** | HTML/CSS/JS + WebSocket client | ✅ Cơ bản |
| **Pipecat** | Real-time voice pipeline framework | ⏸️ Future consideration |

## Cấu trúc thư mục

```
├── app/                     # Ứng dụng Python chính
│   ├── server.py            # Server FastAPI + WebSocket + Kokoro TTS
│   ├── koon_data.py         # Dữ liệu 7 câu hỏi + đáp án + gợi ý
│   ├── scripts/             # Scripts phụ trợ (gen voice, …)
│   └── static/              # Assets tĩnh (index.html)
├── docs/                    # Tài liệu dự án
│   ├── source-brief.md      # Tài liệu tổng hợp yêu cầu
│   └── kich-ban-koon.md     # Kịch bản chi tiết game Koon
├── ref/                     # Reference implementations
│   ├── Kokoro-Vietnamese/   # ✅ Kokoro TTS (ONNX CPU, 14 giọng VN)
│   ├── pipecat/             # ⏸️ Pipecat framework (future)
│   ├── v-tts/               # Voice TTS
│   ├── viet-asr/            # Vietnamese ASR
│   ├── Open-LLM-VTuber/     # VTuber + LLM integration
│   ├── capcut-tts-api/      # CapCut TTS API
│   └── cheap tts/           # Lightweight TTS options
├── thongtin/                # Tài liệu gốc (.docx)
└── _bmad/                   # BMad agent configuration
```

## Cách chạy

```bash
cd "fcode AI siti"

# Cài dependencies
.venv/Scripts/pip install -e ref/Kokoro-Vietnamese[onnx]

# Chạy server
set KOON_VOICE=mai_linh  # tuỳ chọn: mai_linh, diem_trinh, thuc_trinh...
.venv/Scripts/python app/server.py

# Mở http://localhost:8000
```

### Biến môi trường

| Biến | Mặc định | Mô tả |
|---|---|---|
| `KOON_VOICE` | `mai_linh` | Giọng Kokoro TTS (14 giọng VN) |
| `OPENROUTER_API_KEY` | - | API key OpenRouter cho LLM judge |
| `OR_MODEL` | `openai/gpt-4o-mini` | Model OpenRouter |
| `WHISPER_MODEL` | `diepho/PhoWhisper-small-ct2` | Model ASR |

## Tham khảo thêm

- **Pipecat** (`ref/pipecat/`): Framework real-time voice pipeline — xem xét cho phiên bản sau
- **Kokoro Vietnamese** (`ref/Kokoro-Vietnamese/`): TTS tiếng Việt với 14 giọng, chạy ONNX CPU