# Kịch bản AI: Tìm Nắng Cùng AI — Đối kháng nhận diện hình ảnh

> Trò 2 (Tìm Nắng). 3 đội A/B/C đối kháng. AI vision + TTS + WebSocket.
> Tổng thời lượng ~5 phút (6 vòng).
> Cập nhật 2026-07-29: Bỏ auto-timeout — operator (BTC) điều khiển tiến trình bằng nút "Bỏ qua vòng" / "Vòng kế"; vòng cũng tự kết khi cả 3 đội nhận diện đúng. Ép đúng (force_accept) giờ có Kokoro đọc thông báo.

## Cấu trúc

1. **Giới thiệu & khởi động** (~30s) — AI giới thiệu luật chơi.
2. **6 vòng thi** (~4 phút, BTC tự pace):
   - AI công bố vật phẩm cần tìm
   - 3 đội bốc mù trong thùng → giơ trước webcam → bấm NHẬN DIỆN
   - Vision AI chấm đúng/sai → đội đúng được xếp hạng nhất/nhì/ba → cộng điểm
   - Cả 3 đội xong → kết vòng; hoặc BTC bấm "Bỏ qua vòng" / "Vòng kế" (KHÔNG auto-timeout)
3. **Tổng kết & Vô địch** (~30s) — AI tuyên bố đội vô địch + fanfare + banner.

## 6 vật phẩm + vision prompt

> Nguồn: `app/timnang_data.py` (`OBJECTS`).

| # | Vật phẩm | ID | Vision prompt (GPT-4o-mini) |
|---|---|---|---|
| 1 | Quả bóng tennis | `ball` | *"a tennis ball (small, yellow-green, fuzzy)"* |
| 2 | Chai nước Lavie | `lavie` | *"a plastic bottle of Lavie mineral water (clear bottle, blue label, Vietnamese brand)"* |
| 3 | Chai Coca-Cola | `coke` | *"a Coca-Cola bottle or can (red label, Coca-Cola brand)"* |
| 4 | Cái muỗng | `spoon` | *"a spoon (eating utensil)"* |
| 5 | Túi Tote | `tote` | *"a tote bag (cloth/fabric bag with two handles, flat)"* |
| 6 | Cái tô nhựa | `bowl` | *"a plastic bowl (round, colorful)"* |

## 3 đội

| Đội | ID | Màu |
|---|---|---|
| Đội A | `A` | Đỏ `#e74c3c` |
| Đội B | `B` | Xanh dương `#3498db` |
| Đội C | `C` | Xanh lá `#2ecc71` |

## Tính điểm

- **3-2-1**: đội đúng về nhất +3, nhì +2, chót +1.
- Điểm tích luỹ qua 6 vòng. Đội cao nhất cuối cùng → Vô địch.
- Sai không bị trừ điểm — nhắn *"Chưa đúng rồi! Thử lại xem!"* (debounce 1.5s chống spam).

## Lời thoại

### Intro (pre-cache: `intro.wav`)

> "Xin chào các bạn nhỏ! Chào mừng đến với trò chơi Tìm Nắng Cùng AI! Mỗi vòng, AI sẽ gọi tên một vật phẩm. Các đội hãy bốc mù, giơ trước camera rồi bấm nút Nhận Diện. Đội nào đúng trước sẽ được điểm cao hơn. Bắt đầu nhé!"

### Mỗi vòng (pre-cache: `round_{id}.wav`)

> "Vòng {n}! Các đội hãy tìm: {tên vật phẩm}! Nhanh lên nhé, ba, hai, một, bắt đầu!"

### Đúng (pre-cache: `correct_{team_id}_{thứ tự}.wav`)

> "Đội A về nhất!"
> "Đội B về nhì!"
> "Đội C về ba!" (và các hoán vị A/B/C × nhất/nhì/ba)

### Sai (TTS động — Kokoro synthesize)

> "Chưa đúng rồi! Thử lại xem!"

### Tổng kết vòng (TTS động)

> "Hết vòng {N}! Đội A về nhất, tổng 3 điểm. Đội B về nhì, tổng 2 điểm. Đội C chưa kịp."
> (đội chưa nhận diện đúng → "chưa kịp"; đọc theo thứ tự về đích)

### Vô địch (TTS động + fanfare + banner)

> "Xin chúc mừng Đội {tên} đã giành chiến thắng! Các bạn xứng đáng là những nhà Tìm Nắng tài ba! Vỗ tay nào!"

## Công nghệ triển khai

| Thành phần | Chi tiết |
|---|---|
| **Server** | FastAPI + WebSocket (`app/timnang_master.py`). Port **8001** (tách biệt Trò 1 :8000). |
| **Vision AI** | OpenRouter **GPT-4o-mini** (multimodal) — chấm đúng/sai theo `vision_prompt` từng vật. Chấp nhận góc nhìn khác, một phần vật cũng OK. |
| **TTS** | Kokoro Vietnamese (ONNX CPU, giọng `mai_linh`). **Pre-cache** 16 file (intro + 6 vòng + 9 thông báo đúng) → phát tức thì <200ms; fallback synthesize động cho câu không có pre-cache. Gen: `python app/scripts/gen_timnang_voice.py`. |
| **Realtime** | WebSocket master (scoreboard + operator) + 3 stations riêng, push điểm tức thì. |
| **UX sân khấu** | Confetti + chime (Web Audio) khi đúng/về đích; fanfare 7 nốt + banner VÔ ĐỊCH khi kết thúc. |
| **Operator** | Ép đúng (khi AI sai/chậm), ± điểm thủ công, bỏ qua vòng, vòng kế, chạy lại. |
| **Fallback** | Không có `OPENROUTER_API_KEY` → operator duyệt tay (force_accept). Kokoro có sẵn trong venv. |
| **Test** | `python app/scripts/_tn_test.py` — vision + WS flow + recognize round-trip (cần server :8001 đang chạy). |

## WebSocket Protocol

> Chi tiết đầy đủ trong README.md. Tóm tắt:

| Endpoint | Vai trò |
|---|---|
| `/ws/master` | Master/scoreboard + operator |
| `/ws/station/{team}` | Trạm đội (A/B/C) |

### Server → Client

- `{"type": "scoreboard", "phase", "round", "rounds", "object", "teams": [...]}` — đồng bộ trạng thái game.
- `{"type": "round", "object", "vi"}` — gửi station khi mở vòng (tên vật phẩm cần tìm).
- `{"type": "result", "correct", "order", "points", "msg"}` — kết quả nhận diện về trạm.
- `{"type": "play_audio", "key"}` — phát TTS (pre-cache hoặc Kokoro động).
- `{"type": "stop_audio"}` — cắt TTS đang phát (khi operator restart).
- `{"type": "reset"}` | `{"type": "game_over", "winner", "winner_name"}`

### Client → Server

- Trạm: `{"type": "recognize", "image": "data:image/jpeg;base64,..."}`
- Operator: `{"type": "op", "action": "start|restart|skip_round|next_round|force_accept|add_point", "team": "A", "delta": 1}`

## Cách chạy

```bash
# Khởi động server
python app/timnang_master.py

# Master / scoreboard: http://localhost:8001/
# Trạm đội A:         http://<master-ip>:8001/station/A
# Trạm đội B:         http://<master-ip>:8001/station/B
# Trạm đội C:         http://<master-ip>:8001/station/C

# Pre-cache TTS (chạy 1 lần, 16 file)
python app/scripts/gen_timnang_voice.py

# Test
python app/scripts/_tn_test.py
```

## So sánh với kịch bản gốc

| Khía cạnh | Gốc (docx) | Triển khai |
|---|---|---|
| Số đội | 3–4 | 3 (A/B/C) |
| Vật phẩm | 6 món | 6 món (giữ nguyên danh sách gốc) |
| Tính điểm | 3-2-1 | 3-2-1 |
| Nhận diện | TNV quan sát + ghi điểm | AI vision (GPT-4o-mini) tự chấm |
| Gọi vật phẩm | MC hô | AI TTS tự đọc |
| Bảng điểm | Sheet tay | Scoreboard real-time WebSocket |
| Thời gian | 5 phút | ~5 phút (BTC tự pace, 6 vòng) |
| Người hỗ trợ | 3 TNV giám sát + MC | Trẻ tự phục vụ (không TNV) |