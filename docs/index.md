# Tài liệu dự án — fcode AI siti

> Tổng quan các tài liệu trong thư mục `docs/`.

## Tài liệu kịch bản trò chơi

| Tài liệu | Mô tả | Cập nhật |
|---|---|---|
| [`kich-ban-koon.md`](kich-ban-koon.md) | 🎯 **Trò 1 — Cùng Koon Đi Tìm Cầu Vồng**. Kịch bản AI hội thoại: 7 thử thách, pre-cache TTS, Live2D KOON, recap video + magic transition. | 2026-07-28 |
| [`kich-ban-timnang.md`](kich-ban-timnang.md) | 🎯 **Trò 2 — Tìm Nắng Cùng AI**. Kịch bản đối kháng nhận diện hình ảnh: 3 đội A/B/C, vision GPT-4o-mini, WebSocket master + 3 stations, pre-cache TTS, scoreboard. | 2026-07-28 |

## Tài liệu kỹ thuật / nguồn

| Tài liệu | Mô tả | Cập nhật |
|---|---|---|
| [`source-brief.md`](source-brief.md) | 📋 **Tài liệu nguồn tổng hợp**. Ràng buộc dự án, thông số 2 trò chơi, trạng thái triển khai, gaps/câu hỏi mở. Dùng cho BMad agents. | 2026-07-28 |

## Tham khảo nhanh

### Server

| Trò | Port | File chính | Chạy |
|---|---|---|---|
| 1 — Cầu Vồng | `:8000` | `app/server.py` | `python app/server.py` |
| 2 — Tìm Nắng | `:8001` | `app/timnang_master.py` | `python app/timnang_master.py` |

### Pre-cache TTS

| Trò | Script | File gen | Phát tức thì |
|---|---|---|---|
| 1 | `python app/scripts/gen_koon_voice.py` | `app/assets/audio/koon/*.wav` | 28 file |
| 2 | `python app/scripts/gen_timnang_voice.py` | `app/assets/audio/timnang/*.wav` | 16 file |

### Test

| Trò | Chạy | Cần |
|---|---|---|
| 1 | — | — |
| 2 | `python app/scripts/_tn_test.py` | Server :8001 đang chạy |

### Yêu cầu

- `OPENROUTER_API_KEY` — vision (Trò 2) + LLM judge (Trò 1). Không có → operator duyệt tay.
- Kokoro + venv — có sẵn trong `.venv/`.
- Python 3.11+, Windows (đã test).