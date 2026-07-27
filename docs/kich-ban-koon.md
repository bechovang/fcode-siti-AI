# Kịch bản AI: KOON – Cùng Koon Đi Tìm Cầu Vồng

> Nguồn: `thongtin/CÙNG KOO ĐI TÌM CẦU VỒNG.docx` (đã chuyển sang markdown).
> Nhân vật AI tên **KOON**. Trò 1 (Cầu Vồng). Tổng thời lượng ~10–11 phút.
> Cập nhật 2026-07-25: Đã chuyển sang TTS động với **Kokoro Vietnamese** (giọng `mai_linh`).
> Cập nhật 2026-07-28: Pre-cache Kokoro (độ trễ 0) + LLM chấm theo **logic câu đố** & sinh **phản hồi hội thoại** + recap video với transition **"phép màu"** + operator controls ngắt block. Xem README.md để setup đầy đủ.

## Cấu trúc 4 phần
1. **Chào hỏi & khởi động** (~1,5–2 phút) — TTS động
2. **7 thử thách sắc màu** (~6–7 phút) — TTS động từng câu
3. **Chuyển video recap** (~2 phút)
4. **Chào tạm biệt** (~30–40 giây) — TTS động

## 7 câu hỏi + đáp án + gợi ý (đã định nghĩa trong `koon_data.py`)

| # | Mảnh màu | Câu hỏi | Đáp án | Gợi ý khi sai |
|---|---|---|---|---|
| 1 | Đỏ | Trái gì càng chín càng đỏ, bên trong có rất nhiều hạt màu đen? | **Dưa hấu** | Đó là một loại trái cây mùa hè, vỏ xanh ruột đỏ, căng mọng nước |
| 2 | Cam | Cái gì có 4 chân nhưng không biết đi? | **Cái bàn** | Đồ vật có bốn chân, các bạn ngồi học cùng nó mỗi ngày |
| 3 | Vàng | Loài vật nào được mệnh danh là Chúa tể rừng xanh? | **Sư tử** | Loài vật này có bờm to, được mệnh danh là chúa tể rừng xanh |
| 4 | Xanh lá | Con gì mang ngôi nhà trên lưng? | **Ốc sên** | Loài vật này di chuyển rất chậm, lúc nào cũng mang theo ngôi nhà của mình |
| 5 | Xanh dương | Loài hoa nào luôn hướng về phía mặt trời? | **Hoa hướng dương** | Tên của loài hoa này đã nói lên đặc điểm, nó luôn quay về phía mặt trời |
| 6 | Chàm | Mùa nào trong năm thường có thời tiết nóng nhất? | **Mùa hè** | Mùa nóng nhất trong năm, các bạn được nghỉ học và đi chơi |
| 7 | Tím | Sau cơn mưa, điều gì nhiều bạn nhỏ thích ngắm nhất trên bầu trời? | **Cầu vồng** | Đây là một dải màu rất đẹp thường xuất hiện trên bầu trời sau cơn mưa |

**Mỗi thử thách**: đúng → KOON phấn khích + hiệu ứng mảnh màu bay ghép cầu vồng. Sai → KOON khích lệ + **gợi ý**, trẻ thử lại (không bỏ qua).

## Tương tác chờ đáp án
- Phần 1 chờ trẻ đồng thanh "Có!" / "Sẵn sàng!".
- Mỗi thử thách chờ trẻ nói đáp án (→ STT → LLM chấm đúng/sai).
- KOON phản hồi **động** với Kokoro TTS — không pre-cache, mỗi câu nói được sinh realtime.

## Công nghệ triển khai

| Thành phần | Chi tiết |
|---|---|
| **TTS** | Kokoro Vietnamese (ONNX CPU, giọng `mai_linh`). **Pre-cache** toàn bộ câu cố định (intro, câu hỏi, phản hồi đúng, recap, goodbye) → phát tức thì (<200ms); Kokoro động cho câu phản hồi khi sai. Gen: `python app/scripts/gen_koon_voice.py` |
| **LLM** | OpenRouter GPT-4o-mini — 1 call **chấm đúng/sai theo logic câu đố** (chấp nhận nhiều đáp án hợp lý, vd "4 chân không đi" → bàn/ghế/tủ đều đúng) **+ sinh phản hồi hội thoại** khi sai (lễ phép, gợi ý nhẹ, không tiết lộ đáp án, không bịa lý do sai sự thật, an toàn trẻ em). Fallback fuzzy + template khi offline. |
| **ASR** | Web Speech API trong browser (Chrome=Google / Edge=Azure) |
| **Avatar** | Live2D `mao_pro` + lip-sync theo giọng TTS (decode audio → RMS → ParamA) |
| **Recap** | Video `.mp4` bất kỳ trong `app/assets/video/` (ưu tiên `recap.mp4`) + transition "phép màu": KOON bay ra giữa màn + particle sao/bụi cầu vồng + sound magic → flash → video (controls pause/tua/âm lượng). Chưa có video → overlay animation. |
| **Operator** | skip / force_correct / replay / restart — **ngắt được mọi điểm chờ** (ngay cả lúc KOON đang nói hoặc đang chờ trẻ trả lời) |
| **Server** | FastAPI + WebSocket (`app/server.py`) |

### Lời thoại KOON

**Câu cố định** (pre-cache, nguồn: `app/scripts/gen_koon_voice.py` → dict `LINES`, gen ra `app/assets/audio/koon/*.wav`). Khi thiếu file, server tự fallback sang Kokoro động (`say()`) với nội dung tương đương.

**Intro** (5 câu):
- "Hello các bạn nhỏ! Mình là KOON đây! Hôm nay KOON rất vui vì được gặp tất cả các bạn."
- "KOON muốn rủ các bạn đi tìm một điều thật kỳ diệu. Các bạn có thích ngắm cầu vồng không?"
- "Ôa! KOON cũng thích lắm! Nhưng trên đường đến đây, KOON phát hiện cầu vồng đã vô tình làm rơi mất hết các màu sắc rồi. Các bạn có muốn trở thành những nhà thám hiểm nhí và giúp KOON tìm lại 7 sắc màu của cầu vồng không?"
- "Ye! Mình nhớ Chị Gió từng nói... mỗi khi một bạn nhỏ trả lời đúng một câu hỏi thì một sắc màu sẽ quay trở lại... Các bạn đã sẵn sàng đồng hành cùng KOON chưa?"
- "Vậy thì... chuyến phiêu lưu bắt đầu thôi!"

> Lưu ý: KOON được phát âm là **"Cun"** (gen script tự thay `KOON` → `Cun` trước khi TTS).

**Mỗi thử thách:**
- Câu hỏi (pre-cache `q{n}_question`): có câu dẫn cảm xúc theo màu (vd *"Ôa! KOON nhìn thấy mảnh màu đỏ rồi!..."*) + câu đố.
- Câu hỏi chỉ đọc **1 lần**; khi bé sai **không đọc lại** (bấm **R** để đọc lại).
- **Đúng (đáp án dự định)**: pre-cache `q{n}_right` (vd *"Đúng rồi! Chính là quả dưa hấu..."*).
- **Đúng (đáp án thay thế hợp lý)**: LLM sinh reply động xác nhận (vd bé nói "ghế" cho câu "4 chân không đi" → *"Đúng rồi! Ghế cũng có bốn chân và không biết đi!"*).
- **Sai**: LLM sinh reply hội thoại động (vd *"Sao lại là cà chua nhỉ? Cà chua không có vỏ xanh ruột đỏ đâu nha. Để mình gợi ý thêm:..."*). Không tiết lộ đáp án, gợi ý rõ hơn khi sai nhiều lần.

**Recap + Magic** (sau cầu vồng hoàn thiện):
- Pre-cache `90_recap`: *"Ôa! Chúng mình đã làm được rồi! Nhờ sự thông minh và nhiệt tình của các bạn mà cầu vồng đã tìm lại đủ 7 sắc màu..."*
- **Magic reveal**: KOON bay ra giữa màn + particle sao/bụi cầu vồng + sound magic, nói: *"Và bây giờ... cùng KOON ngắm điều kỳ diệu nhé! Các bạn nhắm mắt lại nào... Ba, hai, một... phép màu xuất hiện!"* → flash trắng → phát video recap.

**Outro** (sau video):
- Pre-cache `99_goodbye`: *"Hóa ra điều kỳ diệu mà mình luôn tìm kiếm chính là những nụ cười, những bài học và những kỷ niệm đẹp... KOON chúc các bạn sẽ luôn chăm ngoan, học thật giỏi... Hẹn gặp lại các bạn trong những chuyến phiêu lưu tiếp theo nhé. Tạm biệt các bạn nhỏ!"*
