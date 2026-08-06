"""Regression: path traversal ở GET /audio/{key} (cả 2 server).
Trước fix: key='../../etc/passwd' → os.path.join thoát thư mục → FileResponse serve file tùy ý.
Sau fix: core.audio.safe_audio_key chỉ giữ basename → traversal bị neutralise.
Cả 2 server đều register_audio_route từ core.audio → 1 hàm sanitize duy nhất."""
from core.audio import safe_audio_key


def test_safe_audio_key_blocks_traversal():
    # Path traversal cổ điển (Unix + Windows) → chỉ còn basename
    assert safe_audio_key("../../etc/passwd") == "passwd"
    assert safe_audio_key("..\\..\\windows\\system32\\sam") == "sam"
    assert safe_audio_key("/absolute/secret/path") == "path"
    assert safe_audio_key("..") == ".."                  # basename của '..' = '..' → join thành file vô hại
    # Key hợp lệ giữ nguyên (bỏ đuôi .wav/.mp3)
    assert safe_audio_key("q1_question") == "q1_question"
    assert safe_audio_key("q1_question.wav") == "q1_question"
    assert safe_audio_key("round_ball.mp3") == "round_ball"
    assert safe_audio_key("correct_A_nhat") == "correct_A_nhat"
    assert safe_audio_key("intro") == "intro"


def test_resolve_audio_path_fallback_chain(tmp_path):
    """Verify fallback order: temp TTS wav → pre-cache wav → pre-cache mp3 → None."""
    from core.audio import resolve_audio_path
    tts_dir = tmp_path / "tts"
    audio_dir = tmp_path / "pc"
    tts_dir.mkdir()
    audio_dir.mkdir()
    # Không có gì → None
    assert resolve_audio_path("x", str(tts_dir), str(audio_dir)) is None
    # Pre-cache mp3
    (audio_dir / "intro.mp3").write_bytes(b"")
    r = resolve_audio_path("intro", str(tts_dir), str(audio_dir))
    assert r is not None and r[1] == "audio/mpeg"
    # Pre-cache wav ưu tiên hơn mp3
    (audio_dir / "intro.wav").write_bytes(b"")
    r = resolve_audio_path("intro", str(tts_dir), str(audio_dir))
    assert r is not None and r[1] == "audio/wav"
    # Temp TTS wav ưu tiên nhất
    (tts_dir / "intro.wav").write_bytes(b"")
    r = resolve_audio_path("intro", str(tts_dir), str(audio_dir))
    assert r is not None and str(r[0]).startswith(str(tts_dir))
