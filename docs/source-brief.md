# Tài Liệu Nguồn (Source Brief) — Dự án "fcode AI siti"

> Tài liệu tổng hợp thô để các agent BMad (PM, Analyst, Architect...) tiêu thụ.
> Nguồn gốc: `thongtin/*.docx` (2 bộ tài liệu hướng dẫn trò chơi) + `thongtin/lưu ý.txt` (ràng buộc mới).
> Ngày tổng hợp: 2026-07-25. Cập nhật: 2026-07-25 (TTS integration). Ngôn ngữ: Tiếng Việt.

---

## 0. Bối cảnh dự án

- **Đơn vị thực hiện**: Đội kỹ thuật **F-Code**.
- **Sự kiện**: Gala LHTT **Summer 2026 (SUM26)** — chương trình hè cho các bạn nhỏ tại **Trung tâm Phát huy Bình Thọ**.
- **Mục đích**: Xây dựng phần mềm AI cho phần giao lưu/giải trí trên sân khấu, trẻ em tương tác trực tiếp với AI.
- **Phạm vi (đã chốt)**: Xây dựng **2 trò chơi**.

---

## 1. ⚠️ RÀNG BUỘC THEN CHỐT (ưu tiên cao nhất)

> Nguồn: `thongtin/lưu ý.txt`.

- **Cả 2 trò** phải để **trẻ em tự tương tác hoàn toàn với AI — KHÔNG có người hướng dẫn / MC / TNV tiếp cận hay can thiệp trực tiếp** với trẻ trong khi chơi.
- **Trò 1 (Cầu Vồng)**: AI phải là nhân vật hội thoại **đúng ngữ cảnh với câu trả lời của trẻ, lễ phép (dạ/thưa), câu văn đầy đủ chủ ngữ–vị ngữ**.

### Mâu thuẫn cần giải quyết
Tài liệu gốc (docx) mô tả luồng có **MC điều phối + TNV/trọng tài trực tiếp** (gọi vật phẩm, đưa mic, giám sát máy, ghi điểm). Ràng buộc mới **loại bỏ vai trò người trung gian** này → hệ thống phải **tự vận hành**. Spec PRD/Kiến trúc phải viết theo hướng "AI tự host".

### Hệ quả kỹ thuật bắt buộc
Chuỗi AI hội thoại thời gian thực:
1. **ASR (Speech-to-Text)** — nghe trẻ trả lời (tiếng Việt, giọng trẻ em). *Rủi ro cao: giọng trẻ em tiếng Việt khó nhận.*
2. **LLM hội thoại** — sinh phản hồi đúng context, lễ phép, an toàn cho trẻ, đủ chủ–vị. Cần prompt chặt + guardrail nội dung.
3. **TTS (Text-to-Speech)** — giọng AI tự nhiên, rõ, dễ thương.
4. **UX tự phục vụ** — dẫn dắt trẻ bằng màn hình/giọng/đèn để trẻ biết làm gì tiếp theo khi không có người hỗ trợ vật lý.
5. **Độ trễ thấp** — toàn bộ vòng nghe→suy nghĩ→nói nên ≤ ~2–3 giây (trẻ thiếu kiên nhẫn).

### Trạng thái triển khai hiện tại (Trò 1)

| Thành phần | Giải pháp | Chi tiết |
|---|---|---|
| **TTS** | ✅ **Kokoro Vietnamese** (ONNX CPU) | 14 giọng VN, chạy CPU 5x realtime. Giọng mặc định: `mai_linh` |
| **LLM Judge** | ✅ **OpenRouter GPT-4o-mini** | Chấm đáp án theo logic câu đố, fallback fuzzy match nếu mất kết nối |
| **ASR** | ✅ **Web Speech API** (browser native) | Chrome=Google, Edge=Azure — dùng cho Trò 1 (trẻ nói đáp án) |
| **Server** | ✅ **FastAPI + WebSocket** | `app/server.py` :8000 — 7 thử thách, pre-cache TTS + Kokoro động, operator controls |
| **Frontend** | ✅ **HTML/JS WebSocket client** | Live2D KOON, hiệu ứng cầu vồng, câu hỏi, recap video + magic transition |
| **Avatar** | ✅ **Live2D `mao_pro`** | pixi-live2d-display + lip-sync RMS theo TTS |
| **Pipecat** | ⏸️ **Future consideration** | Framework real-time voice pipeline — đánh giá cho phase 2 |

### Trạng thái triển khai (Trò 2)

| Thành phần | Giải pháp | Chi tiết |
|---|---|---|
| **Server** | ✅ **FastAPI + WebSocket** | `app/timnang_master.py` :8001 — master + 3 stations, operator controls |
| **Vision AI** | ✅ **OpenRouter GPT-4o-mini** (multimodal) | Chấm đúng/sai theo `vision_prompt` từng vật phẩm, chấp nhận góc nhìn thay đổi |
| **TTS** | ✅ **Kokoro Vietnamese** (ONNX CPU) | Pre-cache 16 file (intro + 6 vòng + 9 thông báo), fallback synthesize động |
| **Scoreboard** | ✅ **Real-time WebSocket** | Push điểm mỗi khi có thay đổi, confetti + chime, fanfare vô địch |
| **Frontend** | ✅ **HTML/JS WebSocket client** | `station.html` (webcam + nút NHẬN DIỆN), `master.html` (scoreboard + operator) |
| **Test** | ✅ **`_tn_test.py`** | Vision + WS flow + recognize round-trip |

---

## 2. Trò 1 — "Cùng Hạ Đi Tìm Cầu Vồng" (AI hội thoại)

> Nguồn: `thongtin/_[SITI] TLHD - LHTTSUM26 - AI_ CÙNG HẠ ĐI TÌM CẦU VỒNG...docx` (2 bản trùng nhau).

### Ý tưởng
Trẻ đồng hành cùng **nhân vật AI** vượt qua **7 thử thách** để tìm lại **7 sắc màu cầu vồng**. Mỗi thử thách = 1 câu hỏi đố vui gần gũi. Trả lời đúng → AI mở khóa 1 mảnh màu. Xong 7 thử thách → cầu vồng phát sáng → chuyển **video recap** 1 năm đồng hành.

### Thông số
- Hình thức: tương tác tập thể cùng AI trên màn hình LED lớn.
- Thời lượng: **08–10 phút**.
- Số thử thách: **7** (7 sắc màu).
- Sau thử thách cuối → cầu vồng sáng + ánh sáng/âm thanh → video recap.

### Luật (theo gốc, cần điều chỉnh cho tự vận hành)
- AI đóng vai người bạn đồng hành, dẫn dắt tìm 7 sắc màu.
- AI lần lượt đưa câu hỏi → trẻ (giơ tay) trả lời → AI xác nhận → đúng thì mở khóa mảnh màu.
- Lặp đến đủ 7 màu.

### Yêu cầu kỹ thuật (sau ràng buộc mới)
- **AI nhân vật hội thoại**: tự hỏi, tự nghe trẻ trả lời (ASR), tự phản hồi đúng context + lễ phép + đủ chủ–vị (LLM+TTS), tự kích hoạt hiệu ứng mảnh màu khi đúng.
- **Hiệu ứng hình ảnh**: mở khóa từng mảnh màu, hiệu ứng cầu vồng hoàn thiện.
- **Luồng media**: intro AI → 7 thử thách → cầu vồng → recap video → lời cảm ơn.

### Dụng cụ (gốc)
- 01 màn hình LED/TV lớn.
- 01 video recap.
- Loa + micro.

---

## 3. Trò 2 — "Tìm Nắng Cùng AI" (nhận diện hình ảnh) ✅ Đã hoàn thiện

> Nguồn: `thongtin/[SITI]_TLHD - LHTTSUM26 - I CÙNG .docx`. Triển khai: `app/timnang_master.py` + `app/timnang_data.py` + `app/static/timnang/*.html`.

### Ý tưởng
Trò đối kháng **3 đội** (A/B/C). Mỗi vòng AI gọi tên 1 vật phẩm → trẻ bốc đồ mù trong thùng → giơ trước webcam trạm đội → bấm **NHẬN DIỆN** → AI (vision) chấm đúng/sai → đội đúng trước được điểm cao hơn. **6 vòng = 6 vật phẩm** (~5 phút), điểm theo thứ tự về đích **3-2-1**.

### Thông số
- Hình thức: **3 đội** đối kháng, mỗi đội 1 trạm laptop + webcam. Trẻ **tự phục vụ hoàn toàn**, không TNV/MC.
- Thời lượng: **~5 phút** (6 vòng, BTC tự pace + intro + tổng kết).
- Cách chơi 1 vòng: AI TTS công bố vật phẩm → 3 đội đồng thời bốc mù trong thùng → giơ trước webcam → bấm NHẬN DIỆN → AI vision chấm → đúng → xếp hạng nhất/nhì/ba → cộng điểm.
- Tính điểm **3-2-1**: đội đúng về nhất +3, nhì +2, ba +1.
- Vòng kết thúc khi cả 3 đội đúng, hoặc operator bấm "Bỏ qua vòng" / "Vòng kế" (**KHÔNG auto-timeout**). 6 vòng → tổng kết đội vô địch.

### Giải pháp kỹ thuật
- **Vision**: OpenRouter **GPT-4o-mini** (multimodal) — chấm đúng/sai theo `vision_prompt` mỗi vật. Chấp nhận góc nhìn khác, một phần vật cũng OK.
- **TTS**: Kokoro Vietnamese (giọng `mai_linh`) — **pre-cache** 16 file (intro + 6 vòng + 9 thông báo đúng) + fallback synthesize động.
- **Realtime**: FastAPI + WebSocket (1 master + 3 stations), bảng điểm push tức thì.
- **UX sân khấu**: confetti + chime khi đúng/về đích; fanfare 7 nốt + banner VÔ ĐỊCH khi kết thúc.
- **Server**: Port **8001** (tách biệt Trò 1 :8000).
- **Operator**: ép đúng, ± điểm thủ công, bỏ qua vòng, vòng kế, chạy lại.

### Xử lý khi AI sai/chậm
- Sai → *"Chưa đúng rồi! Thử lại xem!"* (debounce 1.5s chống spam bấm).
- Không có `OPENROUTER_API_KEY` → operator duyệt tay (nút force_accept).
- Mất kết nối → trạm tự dừng, master thông báo.

### Dụng cụ (thực tế)
- 3 thùng vật phẩm bí mật (che kín, khoét lỗ vừa tay) — mỗi đội 1 thùng.
- 6 vật phẩm mô hình (3 bộ giống nhau): **bóng tennis, chai nước, lon nước, muỗng, túi Tote, tô nhựa**.
- 3 laptop/webcam (trạm đội) + 1 màn LED sân khấu (master/scoreboard).
- Server laptop chạy `timnang_master.py`. Điện thoại/tablet có thể dùng làm trạm (PWA webc

---

## 4. Danh sách gaps / câu hỏi mở

1. **Số đội** trò Tìm Nắng: 3 hay 4? (gốc mâu thuẫn).
2. **Spec AI nhận diện**: ngưỡng độ chính xác, độ trễ tối đa, chạy online hay offline (sự kiện wifi yếu), xử lý khi đoán sai.
3. **ASR cho Trò 1**: ✅ Web Speech API (browser native) — Chrome=Google, Edge=Azure. Không cần PhoWhisper offline. Độ chính xác đủ cho 7 đáp án có gợi ý.
4. **LLM/TTS**: ✅ **Đã chọn** Kokoro Vietnamese (TTS, 14 giọng) + OpenRouter GPT-4o-mini (LLM judge). Ràng buộc an toàn nội dung cho trẻ qua system prompt.
5. **Nội dung**: ✅ **Đã có** 7 câu hỏi + gợi ý (`koon_data.py`). ✅ 6 vật phẩm Tìm Nắng + hệ thống điểm 3-2-1 (`timnang_data.py`).
6. **Luồng tự vận hành**: trẻ biết làm gì tiếp theo qua tín hiệu gì (màn hình/đèn/giọng)? có cần onboarding ngắn?
7. **Deadline & ràng buộc sự kiện**: ngày Gala, thời gian dựng/thử nghiệm, ngân sách, thiết bị có sẵn.
8. **Số trạm/lượt chơi song song**: Trò 2 chạy 1 lần trong Gala (6 vòng × 3 đội song song). Trò 1 chạy 1 lần (7 thử thách tập thể).

---

## 5. Tài liệu tham chiếu (nguồn gốc)

- `thongtin/[SITI]_TLHD - LHTTSUM26 - I CÙNG .docx` → Trò 2 (Tìm Nắng).
- `thongtin/_[SITI] TLHD - LHTTSUM26 - AI_ CÙNG HẠ ĐI TÌM CẦU VỒNG I. GIỚI THIỆU TRÒ CHƠI.docx` (+ bản "(1)" trùng) → Trò 1 (Cầu Vồng).
- `thongtin/lưu ý.txt` → Ràng buộc tự tương tác + AI lễ phép.

---

## 6. Trạng thái BMad & Tiến độ

- Dự án ở **Stage 0** (chưa có Project Brief/PRD/Architecture chính thức).
- **Trò 1** (Cầu Vồng): ✅ Hoàn thiện — 7 thử thách, pre-cache TTS + Kokoro động, Live2D KOON + lip-sync, recap video + magic transition, operator controls.
- **Trò 2** (Tìm Nắng): ✅ Hoàn thiện — 3 đội đối kháng, vision GPT-4o-mini, WebSocket master + 3 stations, pre-cache TTS, scoreboard confetti/fanfare.
- **Kế hoạch tiếp theo**: Chạy thử nghiệm với trẻ em, tinh chỉnh prompt KOON, pre-cache edge-tts backup cho Trò 2.
- **Future**: Pipecat framework cho real-time voice pipeline phase 2.
- Cấu hình BMad: `document_output_language = Vietnamese` (đã đặt).
