# Tài Liệu Bàn Giao Vận Hành F-Code SITI AI

Tài liệu này tổng hợp các danh mục cần câu lạc bộ SITI chuẩn bị và những tình huống sân khấu quan trọng cần lưu ý để đảm bảo chương trình chạy mượt mà nhất.

---

## 1. Danh sách cần SITI chuẩn bị (Checklist)

### 💻 Thiết bị Phần cứng
- **01 Máy tính chính (Master Laptop):**
  - Cấu hình: CPU đa nhân (core i5/i7 thế hệ mới hoặc tương đương), RAM tối thiểu 8GB (để chạy mượt model giọng nói AI nội bộ Kokoro).
  - Kết nối: Xuất hình ảnh ra **màn hình LED sân khấu** và xuất âm thanh ra **hệ thống loa**.
  - Trình duyệt bắt buộc: **Google Chrome** hoặc **Microsoft Edge** (để dùng tính năng nhận diện giọng nói).
- **01 Microphone (Trò 1):** Kết nối trực tiếp vào máy tính chính để các bé dùng trả lời câu hỏi AI. Cần test kỹ chống nhiễu/vang từ loa sân khấu (feedback).
- **03 Máy tính xách tay / Tablet cho 3 Đội (Trò 2):**
  - Đặt tại 3 trạm chơi, yêu cầu **bắt buộc phải có Webcam** hoạt động tốt để chụp ảnh vật phẩm.
  - Cả 3 máy này phải dùng chung mạng với Máy tính chính.

### 🌐 Mạng & Kết nối
- **Internet ổn định:** Mặc dù AI giọng nói chạy offline, nhưng tính năng nhận diện hình ảnh (Trò 2), nhận diện giọng nói (Trò 1) và AI suy luận (LLM) vẫn cần Internet.
- **Mạng LAN nội bộ:** Máy tính chính và 3 máy tính của 3 đội cần chung một mạng Wi-Fi/LAN để các máy trạm có thể truy cập IP của máy chính (VD: `http://192.168.1.3:8001/station/A`).
- **Lưu ý cực kỳ quan trọng về HTTPS:** 
  > [!WARNING]
  > Trình duyệt web (Chrome/Edge) sẽ **chặn Webcam và Microphone** nếu truy cập qua IP LAN (`192.168.x.x`) mà không có kết nối bảo mật `HTTPS`.
  > **Giải pháp SITI cần chuẩn bị:** Phải cài đặt Reverse Proxy (như Nginx, Caddy) tích hợp chứng chỉ SSL tự ký (hoặc dùng ngrok/cloudflared) để các máy trạm truy cập qua `https://...`. Nếu chạy bằng `localhost` thì không bị chặn, nhưng máy trạm không thể dùng `localhost` để chọc vào máy chính.

### 🔑 Phần mềm & Tài nguyên
- Đã cài đặt đủ môi trường: **Python 3.10+**.
- File `.env` chứa API Key thật của OpenRouter (`OPENROUTER_API_KEY`) còn đủ credit.
- (Khuyến nghị) Chạy lệnh khởi tạo **sinh giọng pre-cache** trước ở nhà (lệnh `python app/scripts/gen_koon_voice.py` và `gen_timnang_voice.py`) để các câu thoại được tải sẵn, giúp AI phản hồi ngay lập tức <200ms trên sân khấu mà không bị lag chờ sinh giọng.

---

## 2. Các tình huống sân khấu cần lưu ý và Cách xử lý

Người điều khiển (Operator) ngồi tại máy chính cần nắm rõ các công cụ để kiểm soát tình hình nếu có sự cố ngoài ý muốn. Hệ thống không thiết lập "auto-timeout" (tự động đếm ngược hết giờ) mà phụ thuộc hoàn toàn vào quyết định của Operator để linh hoạt với nhịp độ sân khấu.

### Trò 1 (Cầu Vồng)
> [!CAUTION]
> **Tình huống:** Sân khấu quá ồn khiến Microphone nhận diện (STT) sai câu trả lời của bé nhiều lần, hoặc bé nói ngắc ngứ mãi không qua được vòng.
> **Xử lý:** 
> - Operator có thể **gõ trực tiếp đáp án** trên bàn phím máy tính và nhấn Enter thay vì dùng mic.
> - Hoặc nhấn nút **F (Ép đúng)** để hệ thống tự động nhận đáp án là chính xác, bắn pháo giấy và cho bé qua vòng ngay lập tức.
> - Nếu bé nghe chưa rõ câu hỏi, nhấn nút **R (Đọc lại)**.

### Trò 2 (Tìm Nắng)
> [!WARNING]
> **Tình huống 1:** Một đội đưa đồ vật đúng lên nhưng Webcam mờ/góc chụp khuất khiến AI báo Sai liên tục, làm gián đoạn trò chơi.
> **Xử lý:** Operator ngồi máy chính có quyền ấn nút **✓ (Ép đúng / Force Accept)** cho đội đó. Hệ thống sẽ ngay lập tức tính điểm, xếp hạng đội đó và Kokoro AI sẽ đọc tên đội.

> [!TIP]
> **Tình huống 2:** Trò chơi kéo dài quá lâu hoặc một đội không thể tìm thấy đồ vật.
> **Xử lý:** Operator nhấn nút **⏭ Bỏ qua vòng (Skip Round)**. AI sẽ tự động đọc tổng kết điểm hiện tại và chuyển vèo sang vòng tiếp theo mà không đợi đội kia tìm ra.
> - Nếu muốn qua vòng âm thầm (không cần AI tổng kết đọc dài dòng), nhấn **⏭ Vòng kế (Next Round)**.

> [!NOTE]
> **Tình huống 3:** Cộng nhầm điểm hoặc thứ tự.
> **Xử lý:** Operator có thể dùng nút **+1 / -1** trên bảng điều khiển ở máy chính để sửa điểm thủ công (Manual Adjust) mọi lúc.

### 3. Vấn đề mất mạng (Sập mạng đột ngột)
- **Trò 1:** Nhận diện giọng nói STT sẽ hỏng, LLM chấm điểm sẽ hỏng.
  - *Fallback (Dự phòng):* Lúc này, hãy để người vận hành trực tiếp **gõ đáp án** vào máy tính. Hệ thống sẽ tự động dùng tính năng "Fuzzy match" (so sánh chuỗi từ khóa chữ offline) để kiểm tra đáp án đúng mà không cần lên mạng.
- **Trò 2:** Nhận diện ảnh Vision sẽ hỏng.
  - *Fallback:* Operator ngồi dưới tự nhìn mắt thường, thấy đội nào giơ đúng thì nhấn nút **✓ (Ép đúng)** cho đội đó trên bảng điều khiển để chơi tiếp bình thường.

### 4. Lỗi Server / Trình duyệt bị treo
Nếu trong quá trình chơi trình duyệt bị lag cứng hoặc đóng nhầm:
- Không hoảng loạn, chỉ cần mở lại tab (refresh `localhost:8000` hoặc `8001`). Hệ thống có lưu một phần trạng thái.
- Nếu lỡ cổng (port) báo bị kẹt (`address already in use`), bật Task Manager (Windows) để end task Python hoặc chạy lệnh `taskkill` PID của cổng đó theo hướng dẫn trong README.
