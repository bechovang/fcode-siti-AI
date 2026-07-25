# F-Code SITI AI — Summer 2026 Gala

Dự án xây dựng phần mềm AI cho phần giao lưu/giải trí trên sân khấu Gala LHTT **Summer 2026 (SUM26)** tại **Trung tâm Phát huy Bình Thọ**.

Đội ngũ thực hiện: **F-Code**

## Trò chơi

### 1. Cùng Koon Đi Tìm Cầu Vồng (AI hội thoại)

Trẻ đồng hành cùng nhân vật AI **KOON** vượt qua **7 thử thách** để tìm lại 7 sắc màu cầu vồng. Mỗi thử thách là một câu đố. Trả lời đúng → AI mở khóa 1 mảnh màu. Hoàn thành → cầu vồng phát sáng → video recap.

- **Công nghệ**: ASR (giọng trẻ em tiếng Việt) → LLM hội thoại → TTS + hiệu ứng hình ảnh
- **Thời lượng**: ~10–11 phút

### 2. Tìm Nắng Cùng AI (nhận diện hình ảnh)

Trò đối kháng đồng đội. Trẻ bốc đồ mù trong thùng vật phẩm → giơ trước camera → AI nhận diện → đúng thì về đích. Tính điểm 3-2-1.

- **Công nghệ**: Object recognition (AI nhận diện hình ảnh) + bảng điểm real-time
- **Thời lượng**: ~5 phút

## Cấu trúc thư mục

```
├── app/                  # Ứng dụng Python chính
│   ├── server.py         # Server chính (FastAPI/Flask)
│   ├── koon_data.py      # Dữ liệu câu hỏi & kịch bản Koon
│   ├── scripts/          # Scripts phụ trợ (gen voice, …)
│   └── static/           # Assets tĩnh
├── docs/                 # Tài liệu dự án
│   ├── source-brief.md   # Tài liệu tổng hợp yêu cầu
│   └── kich-ban-koon.md  # Kịch bản chi tiết game Koon
├── ref/                  # Reference implementations
│   ├── pipecat/          # Pipecat framework (voice pipeline)
│   ├── v-tts/            # Voice TTS
│   ├── viet-asr/         # Vietnamese ASR
│   ├── Open-LLM-VTuber/  # VTuber + LLM integration
│   ├── capcut-tts-api/   # CapCut TTS API
│   └── cheap tts/        # Lightweight TTS options
├── thongtin/             # Tài liệu gốc (.docx)
└── _bmad/                # BMad agent configuration
```

## Công nghệ tham khảo

- **ASR**: Vietnamese ASR (giọng trẻ em)
- **LLM**: Hội thoại theo ngữ cảnh, lễ phép (dạ/thưa)
- **TTS**: Giọng AI tự nhiên, rõ ràng
- **Real-time pipeline**: Pipecat / Open-LLM-VTuber