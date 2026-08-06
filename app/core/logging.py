"""Setup logging thống nhất — thay thế logging.basicConfig duplicate (server.py:28 == timnang:32)."""
import logging


def setup_logging(name: str, level: int = logging.INFO) -> logging.Logger:
    """Cấu hình root logging 1 lần + trả logger cho module gọi."""
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(message)s")
    return logging.getLogger(name)
