"""FastAPI app factory — thay thế `app = FastAPI(); app.mount('/static', ...)` duplicate.

Trò 1 thêm /live2d + /video mount riêng sau khi tạo app; Trò 2 chỉ cần /static.
(Phase 3 sẽ thu hẹp mount /static của Trò 2 cho đúng scope — hiện giữ nguyên behavior.)
"""
import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles


def create_app(name: str, *, static_dir: str | None = None) -> FastAPI:
    """Tạo FastAPI app + mount /static (nếu thư mục tồn tại)."""
    app = FastAPI(title=name)
    if static_dir and os.path.isdir(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
    return app
