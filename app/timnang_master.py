"""SHIM — Trò 2 (Tìm Nắng). Giữ `python app/timnang_master.py` (:8001) chạy được.

Phase 2: logic giờ nằm trong app/games/timnang/ + app/core/ + app/schemas/.
File này chỉ dựng app + chạy.
- Master/scoreboard/operator: http://localhost:8001/
- Trạm đội: http://localhost:8001/station/A · /B · /C
"""
import os
import sys

# app/ trên sys.path → import được games.timnang + core + schemas
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import constants as C
from core.runtime import run_app
from games.timnang.app import build_app

app = build_app()

if __name__ == "__main__":
    run_app(app, C.GAME2_PORT)
