# Tài Liệu Nguồn (Source Brief) — Dự án "fcode AI siti"

> Tài liệu tổng hợp thô để các agent BMad (PM, Analyst, Architect...) tiêu thụ.
> Nguồn gốc: `thongtin/*.docx` (2 bộ tài liệu hướng dẫn trò chơi) + `thongtin/lưu ý.txt` (ràng buộc mới).
> Ngày tổng hợp: 2026-07-25. Ngôn ngữ: Tiếng Việt.

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

## 3. Trò 2 — "Tìm Nắng Cùng AI" (nhận diện hình ảnh)

> Nguồn: `thongtin/[SITI]_TLHD - LHTTSUM26 - I CÙNG .docx`.

### Ý tưởng
Trò đối kháng đồng đội. Mỗi lượt: trẻ **bốc đồ mù** trong "thùng vật phẩm bí mật" → chạy lên **giơ đồ trước camera** → **AI nhận diện hình ảnh** → đúng thì về đích, đập tay chuyển lượt. Tính điểm theo tốc độ nhận diện đúng.

### Thông số
- Hình thức: **3–4 đội** đối kháng, mỗi đội xếp hàng dọc trước thùng của mình. *(⚠️ Gốc ghi "4 đội/4 thùng" nhưng luật/kịch bản chỉ có **3 đội A,B,C** + 3 TNV giám sát → cần chốt 3 hay 4.)*
- Thời lượng: **5 phút**.
- Cách chơi 1 lượt: gọi tên vật phẩm → bốc mù trong thùng → chạy giơ trước webcam → AI nhận diện đúng → chạy về đích → đập tay → lượt kế.
- Tính điểm **3-2-1**: đội nhận diện đúng về nhất +3, nhì +2, chót +1.
- Hết 5 phút: tổng điểm, cao nhất thắng.

### Yêu cầu kỹ thuật (sau ràng buộc mới)
- **AI nhận diện hình ảnh** (object recognition) cho từng laptop/đội.
- **AI tự host** (không TNV gọi vật phẩm): AI tự thông báo vật phẩm cần tìm, tự nhận diện, tự công bố kết quả **lễ phép, đúng ngữ cảnh**.
- **Bảng điểm thời gian thực** (3-2-1) hiển thị trên màn hình.
- Xử lý khi AI đoán sai / chậm (cần cơ chế rõ).

### Dụng cụ (gốc)
- Thùng vật phẩm bí mật: 03–04 thùng (mỗi đội 1, che kín, khoét lỗ vừa tay).
- Bộ vật phẩm mô hình: 3–4 bộ giống nhau — **bóng tennis, nước Lavie, Coca-Cola, muỗng ngắn, túi Tote, tô nhựa**.
- Laptop: 03–04 cái, mỗi máy 1 module nhận diện + webcam.
- Sheet tính điểm: 01 bảng.

---

## 4. Danh sách gaps / câu hỏi mở

1. **Số đội** trò Tìm Nắng: 3 hay 4? (gốc mâu thuẫn).
2. **Spec AI nhận diện**: ngưỡng độ chính xác, độ trễ tối đa, chạy online hay offline (sự kiện wifi yếu), xử lý khi đoán sai.
3. **Spec ASR cho trẻ em tiếng Việt**: độ chính xác mục tiêu, từ vựng giới hạn, nhiễu sân khấu.
4. **LLM/TTS**: chọn model/nhà cung cấp nào, ràng buộc an toàn nội dung cho trẻ, giọng AI.
5. **Nội dung chưa có**: 7 câu hỏi đố (Cầu Vồng), danh sách vật phẩm chính thức (Tìm Nắng), sheet điểm.
6. **Luồng tự vận hành**: trẻ biết làm gì tiếp theo qua tín hiệu gì (màn hình/đèn/giọng)? có cần onboarding ngắn?
7. **Deadline & ràng buộc sự kiện**: ngày Gala, thời gian dựng/thử nghiệm, ngân sách, thiết bị có sẵn.
8. **Số trạm/lượt chơi song song**: chạy 1 lần hay nhiều lần trong Gala?

---

## 5. Tài liệu tham chiếu (nguồn gốc)

- `thongtin/[SITI]_TLHD - LHTTSUM26 - I CÙNG .docx` → Trò 2 (Tìm Nắng).
- `thongtin/_[SITI] TLHD - LHTTSUM26 - AI_ CÙNG HẠ ĐI TÌM CẦU VỒNG I. GIỚI THIỆU TRÒ CHƠI.docx` (+ bản "(1)" trùng) → Trò 1 (Cầu Vồng).
- `thongtin/lưu ý.txt` → Ràng buộc tự tương tác + AI lễ phép.

---

## 6. Trạng thái BMad

- Dự án ở **Stage 0** (chưa có Project Brief/PRD/Architecture).
- Tài liệu này là **đầu vào thô** cho bước **Project Brief** (agent John — PM, skill `bmad-product-brief`).
- Cấu hình BMad: `document_output_language = Vietnamese` (đã đặt).
