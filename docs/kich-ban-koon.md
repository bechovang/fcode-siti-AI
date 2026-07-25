# Kịch bản AI: KOON – Cùng Koon Đi Tìm Cầu Vồng

> Nguồn: `thongtin/CÙNG KOO ĐI TÌM CẦU VỒNG.docx` (đã chuyển sang markdown).
> Nhân vật AI tên **KOON**. Trò 1 (Cầu Vồng). Tổng thời lượng ~10–11 phút.
> Cập nhật 2026-07-25: Đã chuyển sang TTS động với **Kokoro Vietnamese** (giọng `mai_linh`).

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
| **TTS** | Kokoro Vietnamese (ONNX CPU, 14 giọng). Giọng mặc định: `mai_linh` |
| **LLM Judge** | OpenRouter GPT-4o-mini (hoặc fuzzy match nếu offline) |
| **ASR** | faster-whisper PhoWhisper (CPU int8, VAD filter) |
| **Server** | FastAPI + WebSocket (`app/server.py`) |

### Lời thoại KOON (định nghĩa trong `server.py`)

**Intro:**
- "Xin chào tất cả các bạn nhỏ! Tôi là Koon đây!"
- "Các bạn có biết không, trên bầu trời có một cầu vồng tuyệt đẹp với bảy sắc màu."
- "Nhưng mà ông trời đã lấy mất bảy màu của cầu vồng rồi!"
- "Các bạn hãy giúp tôi tìm lại những mảnh màu đó nhé..."
- "Các bạn đã sẵn sàng chưa? Cùng bắt đầu thôi!"

**Mỗi thử thách:**
- "Câu hỏi thứ [n] màu [tên màu]: [câu hỏi]"
- Đúng: "Chính xác! Đáp án là [answer]. Các bạn giỏi quá! Mảnh màu [màu] đã được tìm thấy!"
- Sai: "Chưa đúng rồi các bạn ơi! Gợi ý nhé: [hint]. Các bạn thử lại xem?"

**Outro:**
- "Cảm ơn tất cả các bạn đã giúp Koon tìm lại đủ bảy sắc màu!..."
- "Cảm ơn các bạn thật nhiều! Hẹn gặp lại vào những lần sau nhé! Tạm biệt!"
