"""
Pre-cache giọng KOON (Trò Cầu Vồng) — engine Kokoro (mặc định) hoặc edge-tts (backup).
Chạy:  python app/scripts/gen_koon_voice.py
Chọn engine:  KOON_GEN_ENGINE=kokoro (mặc định)  |  KOON_GEN_ENGINE=edge
  - kokoro: Kokoro-Vietnamese (ONNX CPU), giọng `mai_linh` → output .wav 24kHz (nhất quán với TTS động).
  - edge:   edge-tts vi-VN-HoaiMyNeural (cần mạng, free) → output .mp3 (backup tier thấp hơn).

Output: app/assets/audio/koon/<key>.{wav|mp3} — phát local tại Gala (không cần mạng khi đã gen xong).

LINES là nguồn sự thật duy nhất cho nội dung thoại (dùng chung cho cả 2 engine).
"""
import os
import sys

ENGINE = os.environ.get("KOON_GEN_ENGINE", "kokoro").strip().lower()
OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "audio", "koon")
OUT = os.path.abspath(OUT)

# Toàn bộ câu thoại cố định của KOON (nguồn: docs/kich-ban-koon.md)
LINES = {
    # --- Phần 1: Chào & khởi động ---
    "01_intro_greet": "Hello các bạn nhỏ! Mình là KOON đây! Hôm nay KOON rất vui vì được gặp tất cả các bạn.",
    "02_intro_rainbow_q": "KOON muốn rủ các bạn đi tìm một điều thật kỳ diệu. Các bạn có thích ngắm cầu vồng không?",
    "03_intro_lost_colors": "Ôa! KOON cũng thích lắm! Nhưng trên đường đến đây, KOON phát hiện cầu vồng đã vô tình làm rơi mất hết các màu sắc rồi. Các bạn có muốn trở thành những nhà thám hiểm nhí và giúp KOON tìm lại 7 sắc màu của cầu vồng không?",
    "04_intro_rule": "Ye! Mình nhớ Chị Gió từng nói với mình rằng: mỗi khi một bạn nhỏ trả lời đúng một câu hỏi thì một sắc màu sẽ quay trở lại với cầu vồng. Chỉ cần chúng mình tìm đủ 7 màu thì điều kỳ diệu sẽ xuất hiện. Các bạn đã sẵn sàng đồng hành cùng KOON chưa?",
    "05_intro_start": "Vậy thì... chuyến phiêu lưu bắt đầu thôi!",
    # --- Thử thách 1: Đỏ ---
    "q1_question": "Ôa! KOON nhìn thấy mảnh màu đỏ rồi! Các bạn giúp mình nhé! Câu hỏi là: Trái gì càng chín càng đỏ, bên trong có rất nhiều hạt màu đen?",
    "q1_right": "Đúng rồi! Chính là quả dưa hấu. Các bạn giỏi quá! Chúng mình đã tìm lại được mảnh màu đỏ đầu tiên rồi!",
    "q1_wrong": "Gần đúng rồi nè! Các bạn suy nghĩ thêm một chút nhé. Trái cây này rất mát, thường xuất hiện vào mùa hè và bên trong có rất nhiều hạt màu đen.",
    # --- Thử thách 2: Cam ---
    "q2_question": "Ye! Cầu vồng đã có màu đầu tiên rồi! Chúng mình tiếp tục tìm mảnh màu cam nhé. Nhưng mảnh màu này đang trốn sau một câu đố đấy. Câu hỏi là: Cái gì có 4 chân nhưng không biết đi?",
    "q2_right": "Chính xác! Đó là cái bàn. Mảnh màu cam đã quay trở lại rồi. Các bạn làm tốt lắm!",
    "q2_wrong": "Không sao đâu! Đây là một đồ vật mà ngày nào các bạn cũng ngồi học cùng đấy.",
    # --- Thử thách 3: Vàng ---
    "q3_question": "Ôa! Bây giờ KOON nhìn thấy mảnh màu vàng ở phía trước. Muốn lấy được màu vàng, chúng mình hãy cùng trả lời câu hỏi này nhé. Loài vật nào được mệnh danh là Chúa tể rừng xanh?",
    "q3_right": "Đúng rồi! Chính là sư tử. Các bạn thật thông minh! Màu vàng đã trở về với cầu vồng.",
    "q3_wrong": "Con vật này có chiếc bờm rất to và thường xuất hiện trong rừng.",
    # --- Thử thách 4: Xanh lá ---
    "q4_question": "Chúng mình đi được hơn nửa chặng đường rồi. Mảnh màu xanh lá đang chờ các bạn phía trước. Câu hỏi là: Con gì mang ngôi nhà trên lưng?",
    "q4_right": "Chính xác! Đó là ốc sên. Các bạn giỏi quá! Chỉ còn vài màu nữa thôi!",
    "q4_wrong": "Con vật này di chuyển rất chậm và lúc nào cũng mang chiếc vỏ trên lưng.",
    # --- Thử thách 5: Xanh dương ---
    "q5_question": "Ôa! KOON đã nhìn thấy màu xanh dương rồi. Các bạn giúp mình lấy lại màu này nhé. Câu hỏi là: Loài hoa nào luôn hướng về phía mặt trời?",
    "q5_right": "Đúng rồi! Chính là hoa hướng dương. Cầu vồng của chúng mình sắp hoàn thành rồi!",
    "q5_wrong": "Tên của loài hoa này đã nói lên đặc điểm của nó rồi đấy.",
    # --- Thử thách 6: Chàm ---
    "q6_question": "Chỉ còn hai mảnh màu nữa thôi! Các bạn cố lên nhé! Câu hỏi lần này là: Mùa nào trong năm thường có thời tiết nóng nhất?",
    "q6_right": "Đúng rồi! Đó là mùa hè. Chúng mình sắp hoàn thành nhiệm vụ rồi!",
    "q6_wrong": "Đây cũng chính là mùa mà các bạn đang được nghỉ học và vui chơi.",
    # --- Thử thách 7: Tím ---
    "q7_question": "Đây là mảnh màu cuối cùng! Chỉ cần tìm được màu này, cầu vồng sẽ trở lại. Các bạn hãy trả lời thật to để cả bầu trời đều nghe thấy nhé! Câu hỏi là: Sau cơn mưa, điều gì mà rất nhiều bạn nhỏ thích ngắm nhất trên bầu trời?",
    "q7_right": "Chính xác! Đó là cầu vồng! Chúng mình đã tìm lại đủ 7 sắc màu rồi!",
    "q7_wrong": "Đó là một dải màu rất đẹp thường xuất hiện sau cơn mưa.",
    # --- Phần 3: Recap ---
    "90_recap": "Ôa! Chúng mình đã làm được rồi! Nhờ sự thông minh và nhiệt tình của các bạn mà cầu vồng đã tìm lại đủ 7 sắc màu. Các bạn có muốn xem điều kỳ diệu ấy là gì không? Vậy hãy cùng KOON đón chờ điều kỳ diệu ấy nhé!",
    # --- Phần 4: Tạm biệt ---
    "99_goodbye": "Hóa ra điều kỳ diệu mà mình luôn tìm kiếm chính là những nụ cười, những bài học và những kỷ niệm đẹp mà chúng mình đã cùng nhau tạo nên. Cảm ơn các bạn vì đã đồng hành cùng KOON và giúp cầu vồng rực rỡ trở lại. KOON chúc các bạn sẽ luôn chăm ngoan, học thật giỏi, luôn vui vẻ và giữ thật nhiều ước mơ để tiếp tục khám phá thế giới. Hẹn gặp lại các bạn trong những chuyến phiêu lưu tiếp theo nhé. Tạm biệt các bạn nhỏ!",
}


def _normalize(text: str) -> str:
    """KOON đọc là 'Cun' (KOON chỉ là cách viết). Áp dụng cho cả 2 engine."""
    return text.replace("KOON", "Cun")


# ---------------------------------------------------------------- Kokoro (.wav)
def gen_kokoro():
    import soundfile as sf
    from kokoro_vietnamese import KokoroVietnamese as KokoroTTS

    voice = os.environ.get("KOON_VOICE", "mai_linh")
    tts = KokoroTTS(device="cpu", voice=voice)
    os.makedirs(OUT, exist_ok=True)
    ok, fail = 0, 0
    for key, text in LINES.items():
        path = os.path.join(OUT, f"{key}.wav")
        try:
            audio, _phonemes = tts.synthesize(_normalize(text))
            sf.write(path, audio, 24000)
            print(f"OK   {key}")
            ok += 1
        except Exception as e:
            print(f"FAIL {key}: {e}")
            fail += 1
    print(f"\nKokoro [{voice}] xong: {ok} OK, {fail} FAIL — output: {OUT}")
    if fail:
        sys.exit(1)


# ------------------------------------------------------------------ edge (.mp3)
def gen_edge():
    import asyncio
    import edge_tts

    VOICE = os.environ.get("KOON_VOICE_EDGE", "vi-VN-HoaiMyNeural")
    RATE = os.environ.get("KOON_RATE", "-5%")

    async def _run():
        os.makedirs(OUT, exist_ok=True)
        ok, fail = 0, 0
        for key, text in LINES.items():
            path = os.path.join(OUT, f"{key}.mp3")
            try:
                comm = edge_tts.Communicate(_normalize(text), VOICE, rate=RATE)
                await comm.save(path)
                print(f"OK   {key}")
                ok += 1
            except Exception as e:
                print(f"FAIL {key}: {e}")
                fail += 1
        print(f"\nEdge [{VOICE}] xong: {ok} OK, {fail} FAIL — output: {OUT}")
        if fail:
            sys.exit(1)

    asyncio.run(_run())


if __name__ == "__main__":
    print(f"Engine: {ENGINE}  |  output dir: {OUT}")
    if ENGINE == "edge":
        gen_edge()
    elif ENGINE == "kokoro":
        gen_kokoro()
    else:
        print(f"ENGINE không hợp lệ: {ENGINE} (dùng 'kokoro' hoặc 'edge')")
        sys.exit(2)
