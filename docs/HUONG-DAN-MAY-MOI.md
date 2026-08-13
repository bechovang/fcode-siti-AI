# 🖥️ Hướng dẫn cài đặt từ đầu cho máy mới

Cài đặt toàn bộ dự án **F-Code SITI AI (Gala Summer 2026)** trên một máy mới, từ con số 0
đến khi chạy được cả **2 trò chơi**:

| | Trò chơi | Đường dẫn | Cổng |
|---|---|---|---|
| **1** | Cùng Koon Đi Tìm Cầu Vồng (trò hỏi-đáp, mic) | `app/server.py` | `8000` |
| **2** | Tìm Nắng Cùng AI (nhận diện ảnh, 3 đội) | `app/timnang_master.py` | `8001` |

> 📌 Hai trò chạy **2 cổng riêng**, cài đặt chung cho cả hai — chỉ lệnh **chạy** ở cuối là khác.
> Máy chính có thể chạy cả 2 trò cùng lúc.

---

## ⏱️ Tổng thời gian (máy mới, internet tốt)

| Giai đoạn | Thời gian |
|---|---|
| Cài Python + Git | ~5 phút |
| Clone + cài thư viện Python | ~5–10 phút |
| Cài Kokoro TTS (~2GB, nặng nhất) | **~10–20 phút** |
| Tạo `.env` + API key | ~5 phút |
| Sinh pre-cache giọng (1 lần) | ~5–15 phút |
| **Tổng lần đầu** | **~30–60 phút** |
| Lần sau chạy lại | < 1 phút |

---

## ⚠️ 2 lỗi "bẫy người mới" hay quên nhất

Hai việc **dễ quên nhất** — bỏ qua thì game *vẫn chạy được* nhưng trải nghiệm kém:

1. **Quên sinh giọng pre-cache**: `python app/scripts/gen_koon_voice.py` (và `gen_timnang_voice.py`).
   - Quên thì **KHÔNG có tiếng** KOON/tổng kết (chỉ có chữ; game vẫn chơi được vì tự synthesize chậm).
   - → Xem **Bước 6**.
2. **Quên tải avatar 2.5D (Live2D) cho KOON**: `git clone https://github.com/Open-LLM-VTuber/Open-LLM-VTuber.git ref/Open-LLM-VTuber`.
   - Quên thì KOON chỉ là **emoji 🦊**, không có hình người nói chuyện.
   - → Xem **Bước 4.5**.

---

## ✅ 1. Cài đặt công cụ cần thiết trước

### Yêu cầu tối thiểu

- **Python 3.10 trở lên** (máy test dùng 3.11)
- **Git**
- **Chrome hoặc Edge** (bắt buộc — đọc mic/STT Trò 1, webcam Trò 2)
- **Internet** lúc cài (pip, Kokoro, gen giọng edge, chạy LLM/vision OpenRouter, STT). Sau khi gen giọng xong, game vẫn chạy offline được ở chế độ dự phòng.
- **RAM ≥ 4GB** (khuyến nghị 8GB+), ~3GB ổ trống
- **API key OpenRouter** (khuyến nghị mạnh, đăng ký miễn phí tại https://openrouter.ai )

### Cài Python (Windows)

1. Tải tại https://www.python.org/downloads/
2. Khi cài: **phải tick** ô **"Add Python to PATH"**.
3. Kiểm tra: mở `cmd` (hoặc PowerShell) gõ:
   ```cmd
   python --version
   ```
   → hiện `Python 3.11.x` hoặc tương đương.

### Cài Git (Windows)

1. Tải tại https://git-scm.com/download/win (bản 64-bit).
2. Cài mặc định (next next...). Kiểm tra:
   ```cmd
   git --version
   ```

---

## 📦 2. Clone dự án (lấy mã nguồn về máy)

Mở `cmd` / PowerShell tại thư mục bạn muốn đặt dự án, rồi gõ:

```cmd
git clone https://github.com/bechovang/fcode-siti-AI.git
cd fcode-siti-AI
```

> ℹ️ Trong repo có 1 **submodule** tên `ref/Kokoro-Vietnamese` (thư viện TTS tiếng Việt).
> Nếu clone kiểu thường ở trên, thư mục đó sẽ **trống** — phải chạy lệnh cập nhật submodule
> ở dưới. (Nếu clone bằng `--recurse-submodules` thì nó tự tải, không cần bước này.)

### Cập nhật submodule Kokoro TTS

```cmd
git submodule update --init --recursive
```

> ⚠️ Model ONNX của Kokoro (~2GB) sẽ **tự download lần đầu** khi chạy server hoặc gen giọng.
> Nếu clone repo bằng **ZIP** (tải từ web) thay vì `git clone`, submodule sẽ trống → Kokoro không chạy.

---

## 🐍 3. Tạo môi trường ảo (venv)

Môi trường ảo để cài thư viện riêng cho dự án, không làm loạn Python toàn máy.

```cmd
python -m venv .venv
.venv\Scripts\activate
```

> Nếu PowerShell báo **lỗi chạy script bị chặn**:
> ```powershell
> Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
> .venv\Scripts\Activate.ps1
> ```

Sau khi activate, dấu nhắc đầu dòng sẽ hiện **`(.venv)`**.
> ⚠️ **Mỗi lần mở terminal mới phải activate lại** trước khi chạy các lệnh pip/python phía dưới.

---

## 📚 4. Cài đặt thư viện Python

### a) Cài Kokoro Vietnamese TTS (phần nặng nhất, ~vài GB)

```cmd
pip install -e "ref/Kokoro-Vietnamese[onnx]"
```

- **Thời gian**: lần đầu **5–15 phút** (tải `torch`, `transformers`, `onnxruntime`).
- **Mạng yếu?** cài từng gói trước cho chắc: `pip install torch` xong mới chạy lệnh trên.
- **Kiểm tra**: gõ lệnh dưới, nếu in chữ `OK` là được:
  ```cmd
  python -c "from kokoro_vietnamese import KokoroVietnamese; print('OK')"
  ```

### b) Cài các thư viện còn lại (cả 2 trò)

```cmd
pip install -r app/requirements.txt
```

Gồm: `fastapi`, `uvicorn`, `openai` (chấm đáp án / vision), `rapidfuzz`, `soundfile`.

### c) Cài thêm để chạy test tự động Trò 2 (tùy chọn)

```cmd
pip install websockets pillow
```

---

## 🦊 4.5. Tải avatar 2.5D (Live2D) cho KOON — hay quên! (Trò 1)

KOON có một **nhân vật 2.5D** (hình người nói chuyện, cử động môi theo giọng). Thư mục chứa model
này `ref/Open-LLM-VTuber/` **bị gitignore** (có cả `.git` nội bộ, cồng kềnh) nên **máy mới clone xong
sẽ KHÔNG có** — phải tải riêng bằng lệnh:

```cmd
git clone https://github.com/Open-LLM-VTuber/Open-LLM-VTuber.git ref/Open-LLM-VTuber
```

> 🦊 **Quên làm bước này → KOON chỉ hiện emoji 🦊** (vẫn chơi đầy đủ, chỉ mất hình người).
> Cài xong, **restart server** → log hiện `Live2D: /live2d (mao_pro)` và `/health` trả `"live2d": true`.

---

## 🌈 5. Tạo file `.env` và điền API key

Trò 1 cần LLM chấm đáp án, Trò 2 cần vision chấm ảnh — cả hai dùng chung `OPENROUTER_API_KEY`.

### a) Tạo file `.env` từ mẫu có sẵn

```cmd
copy .env.example .env
```
(PowerShell: `Copy-Item .env.example .env` · Linux/mac: `cp .env.example .env`)

### b) Mở file `.env` và sửa dòng key

```env
OPENROUTER_API_KEY=sk-or-v1-XXXXXXXXXX   ← thay bằng key thật của bạn
```

- Key lấy miễn phí tại: https://openrouter.ai → tài khoản → *Settings* → *Keys*.
- Các biến khác (`OR_MODEL`, `KOON_VOICE`, `KOON_GEN_ENGINE`...) **cứ để mặc định** là chạy được ngay.
- Không có key thì vẫn chạy ở chế độ dự phòng (xem **Troubleshooting** ở cuối).

> 🔒 File `.env` đã được `.gitignore` — **không bao giờ** bị đẩy lên GitHub. Chỉ `.env.example`
> (giá trị rỗng) mới được commit. Tuyệt đối không commit key thật.

---

## 🔊 6. Sinh pre-cache giọng nói (chạy 1 lần) — HAY QUÊN!

> ⚠️ **Đây là bước hay quên nhất.** Bỏ qua thì game chạy nhưng **KHÔNG có tiếng**.
> Sau khi chạy xong, nhớ **kiểm tra thư mục có file sinh ra** (lệnh ở cuối mục).

Toàn bộ câu thoại cố định được **pre-cache** bằng giọng Kokoro để phát **tức thì** (<200ms)
thay vì synthesize mỗi lần (chậm ~1–2s). Các file nằm trong `app/assets/audio/` (**đã gitignore**,
không theo repo) nên **máy mới phải tự gen**.

```cmd
rem Trò 1 — KOON
python app/scripts/gen_koon_voice.py

rem Trò 2 — Tìm Nắng
python app/scripts/gen_timnang_voice.py
```

Kết quả:
- `app/assets/audio/koon/*.wav`
- `app/assets/audio/timnang/*.wav`

**Muốn chắc chắn đã có tiếng (kiểm tra nhanh):**
```cmd
dir app\assets\audio\koon
dir app\assets\audio\timnang
```
→ Nhìn thấy nhiều file `.wav` là đã gen xong, sẵn sàng phát tiếng.

> **Bỏ qua bước này vẫn chạy được** — server tự synthesize Kokoro động từng câu (chậm hơn,
> nhưng game vẫn hoạt động đầy đủ). Khuyến nghị mạnh nên gen để biểu diễn mượt.

---

## ▶️ 7. Chạy trò chơi

### Trò 1 — Cầu Vồng (port 8000)

```cmd
python app/server.py
```

Log kỳ vọng:
```
INFO LLM judge: OpenRouter openai/gpt-4o-mini
INFO Kokoro TTS sẵn sàng (giọng mai_linh, device=cpu)
INFO Uvicorn running on http://0.0.0.0:8000
```

→ Mở **http://localhost:8000** bằng **Chrome/Edge**:
- Bấm **"🧪 Test mic / STT"** để kiểm tra giọng nói.
- Bấm **"Bắt đầu"** → KOON chào và đặt câu hỏi.

### Trò 2 — Tìm Nắng (port 8001)

```cmd
python app/timnang_master.py
```

→ Mở:
| Trang | URL |
|---|---|
| Master / bảng điểm / operator | http://localhost:8001/ |
| Trạm đội A / B / C (webcam) | http://localhost:8001/station/A · /B · /C |

- **Test 1 máy**: mở master + 3 trạm bằng `localhost` (4 tab) là chơi đủ.
- **Gala nhiều máy**: master trên máy chính; trạm mở trên laptop đội bằng **IP LAN** máy master,
  vd `http://192.168.1.3:8001/station/A` (tìm IP bằng `ipconfig` → dòng IPv4).
  > ⚠️ Webcam cần secure-context: trạm mở bằng IP LAN thường sẽ bị chặn webcam. Phải chạy qua
  > **HTTPS** cho sân khấu thật (xem Troubleshooting).

### Chạy cả 2 trò cùng lúc

Mở **2 terminal riêng** (mỗi cái activate venv rồi chạy 1 server):

```cmd
rem Terminal 1 — Trò 1
python app/server.py           rem :8000

rem Terminal 2 — Trò 2
python app/timnang_master.py   rem :8001
```

---

## 🧪 8. Kiểm tra trạng thái

```cmd
curl http://localhost:8000/health    rem Trò 1 → {"tts":true,"llm":true,...}
curl http://localhost:8001/health    rem Trò 2 → {"vision":true,"tts":true,...}
```

Test tự động Trò 2 (cần server :8001 đang chạy + đã cài `websockets`/`pillow`):
```cmd
python app/scripts/_tn_test.py
```

---

## ❓ 9. Troubleshooting

### "Kokoro Vietnamese chưa cài" khi chạy server
```cmd
pip install -e "ref/Kokoro-Vietnamese[onnx]"
```

### Lỗi "address already in use" (port 8000 / 8001 bị chiếm)
```cmd
netstat -ano | findstr :8000     rem Trò 1 ; hoặc :8001 cho Trò 2
taskkill /PID <PID> /F
```

### Không có OpenRouter key — có chạy được không?
Có, ở chế độ dự phòng:
- **Trò 1**: chấm đáp án bằng **fuzzy match** (kém chính xác hơn LLM).
- **Trò 2**: vision tắt → operator **duyệt đúng/sai bằng tay** (nút *Ép đúng*).

### Mic / STT không nhận giọng nói
- Dùng **Chrome hoặc Edge** (Firefox/Safari cũng có thể không hỗ trợ Web Speech API).
- Cấp quyền mic cho site (icon khoá/mic ở góc trình duyệt).
- Cần **internet** (STT gửi audio lên Google/Azure).
- Truy cập bằng IP thay vì `localhost` → phải dùng **HTTPS**.
- Bấm **"🧪 Test mic"** ở màn start để kiểm tra nhanh.

### KOON vẫn là emoji 🦊 (thiếu avatar Live2D)
Thư mục `ref/Open-LLM-VTuber/` **gitignore** nên không có sau khi clone mới — game **tự fallback
về emoji 🦊**, vẫn chơi bình thường. Muốn có avatar động:
```cmd
git clone https://github.com/Open-LLM-VTuber/Open-LLM-VTuber.git ref/Open-LLM-VTuber
```
Rồi restart server.

### Giọng bị "robot" / đã gen giọng nhưng không có tiếng
- Kiểm tra đã gen pre-cache: `app\assets\audio` phải có file `.wav` (nếu không → chạy lại Bước 6).
- Thử đổi giọng trong `.env`: `KOON_VOICE=thuc_trinh` (hoặc `storyvert` — kể chuyện, cảm xúc hơn).

### Webcam trạm đội bị chặn khi dùng IP LAN
Webcam chỉ mở qua **localhost hoặc HTTPS**. Để chơi nhiều máy trên sân khấu thật, phải chạy server
qua **HTTPS**: đặt reverse proxy (ví dụ **Caddy** / **Nginx**) phía trước, cấp chứng chỉ SSL tự do
(Let's Encrypt), rồi trạm truy cập `https://<domain>/station/A`. Test tạm trên 1 máy thì cứ dùng `localhost`.

---

## 📁 10. Tài liệu khác trong repo

| Tài liệu | Nội dung |
|---|---|
| `README.md` | Tổng quan đầy đủ + chức năng UI/UX + chi tiết kỹ thuật |
| `docs/kich-ban-koon.md` | Kịch bản chi tiết Trò 1 |
| `docs/kich-ban-timnang.md` | Kịch bản chi tiết Trò 2 |
| `docs/source-brief.md` | Tổng hợp yêu cầu |
| `thongtin/` | Tài liệu gốc (.docx) |

---

## 🏗️ 11. Cấu trúc thư mục (tóm tắt)

```
fcode-siti-AI/
├── app/
│   ├── server.py               # 🎯 Trò 1 (:8000)
│   ├── koon_data.py            # dữ liệu 7 câu hỏi Trò 1
│   ├── timnang_master.py       # 🎯 Trò 2 (:8001)
│   ├── timnang_data.py         # dữ liệu 6 vật phẩm Trò 2
│   ├── requirements.txt        # thư viện Python
│   ├── assets/audio/           # 🔊 giọng pre-cache (gitignore — tự gen)
│   ├── scripts/                # gen giọng + test
│   └── static/                 # giao diện web (index.html, timnang/)
├── docs/                       # tài liệu (có file này)
├── ref/Kokoro-Vietnamese/      # ✅ TTS tiếng Việt (submodule)
└── thongtin/                   # tài liệu gốc .docx
```