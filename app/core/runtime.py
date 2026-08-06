"""Runtime — thay thế uvicorn runner duplicate (server.py:495-497 == timnang_master.py:447-449)."""
from . import constants as C


def run_app(app, port: int) -> None:
    """Chạy FastAPI app qua uvicorn trên HOST:port (entry point duy nhất)."""
    import uvicorn
    uvicorn.run(app, host=C.HOST, port=port, log_level="info")
