"""SHIM — Trò 1 (Cầu Vồng). Giữ `python app/server.py` (:8000) chạy được (README + muscle memory).

Phase 2: logic giờ nằm trong app/games/cau_vong/ + app/core/ + app/schemas/.
File này chỉ dựng app + chạy. Mở http://localhost:8000 bằng Chrome/Edge.
"""
import os
import sys

# app/ trên sys.path → import được games.cau_vong + core + schemas (cùng cấu trúc cũ)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import constants as C
from core.runtime import run_app
from games.cau_vong.app import build_app

app = build_app()

if __name__ == "__main__":
    run_app(app, C.GAME1_PORT)
