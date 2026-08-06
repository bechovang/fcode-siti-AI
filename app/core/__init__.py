"""app.core — shared infrastructure cho cả 2 trò (Cầu Vồng + Tìm Nắng).

Trích xuất từ code duplicate giữa app/server.py và app/timnang_master.py:
config, constants, paths, logging, LLM client, Kokoro TTS provider, audio route,
WS helpers, FastAPI app factory, runtime. Giết ~60% trùng lặp + 4 drift bug tại gốc.

Các module dùng relative import (`from .xxx import`) — core là package, import qua
`from core.yyy import zzz` (app/ phải nằm trên sys.path, cả 2 server + test đều đảm bảo).
"""
