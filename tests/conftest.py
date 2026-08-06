"""Pytest config — đưa app/ vào sys.path để test import được các module sibling
(server, timnang_master, koon_data, timnang_data) mà không cần cài package.

Test chạy KHÔNG cần Kokoro: kokoro_vietnamese không cài → TTS_AVAILABLE/_TTS_OK=False
→ get_tts() trả None, không load model ONNX. OPENROUTER_API_KEY không set → llm=None.
"""
import os
import sys

_APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app"))
if _APP_DIR not in sys.path:
    sys.path.insert(0, _APP_DIR)
