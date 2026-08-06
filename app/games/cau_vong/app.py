"""Composition root Trò 1 — build_app() dựng FastAPI app with MVC architecture.

Tách side-effect ra khỏi import: warmup TTS + tạo OpenRouter client + tempdir chỉ chạy
trong build_app() (không lúc import module) → module import được trong test không load Kokoro.
Entry point cũ (app/server.py) là shim gọi build_app() + run_app().
"""
import os

from core import paths, tts
from core.app_factory import create_app
from core.audio import register_audio_route
from core.config import settings
from core.llm import make_openrouter_client
from core.logging import setup_logging
from fastapi.staticfiles import StaticFiles
import koon_data as data_source

# MVC imports
from games.cau_vong.repositories import ChallengeRepository, ScriptRepository
from games.cau_vong.services import JudgeService, TTSService, SessionManager, GameFlowService
from games.cau_vong.controllers import CauVongWebSocketController, HealthController

log = setup_logging("koon")


def build_app():
    TTS_DIR = paths.new_tts_dir("koon_tts_")
    log.info("TTS temp dir: %s", TTS_DIR)

    llm = make_openrouter_client()
    log.info("LLM judge: %s", "OpenRouter " + settings.or_model if llm else "TẮT — dùng fuzzy match")

    if not tts.tts_available():
        log.warning("kokoro-vietnamese chưa cài — chạy pip install -e .[onnx] trong ref/Kokoro-Vietnamese")
    tts.warmup()  # load model ngay lúc boot (tránh lazy-init block lần say() đầu)

    log.info("STT: browser Web Speech API (Chrome=Google / Edge=Azure)")

    app = create_app("Cầu Vồng (KOON)", static_dir=paths.STATIC_DIR)

    # Live2D models (ref/Open-LLM-VTuber — gitignored; fallback emoji 🦊 nếu thiếu)
    live2d_available = os.path.isdir(paths.LIVE2D_DIR)
    if live2d_available:
        app.mount("/live2d", StaticFiles(directory=paths.LIVE2D_DIR), name="live2d")
        log.info("Live2D: /live2d (mao_pro) — từ ref/Open-LLM-VTuber/live2d-models")
    else:
        log.warning("Live2D: thiếu ref/Open-LLM-VTuber/live2d-models — avatar dùng fallback emoji 🦊")

    # Recap video
    if os.path.isdir(data_source.VIDEO_DIR):
        app.mount("/video", StaticFiles(directory=data_source.VIDEO_DIR), name="video")
        _mp4s = [f for f in os.listdir(data_source.VIDEO_DIR) if f.lower().endswith(".mp4")]
        log.info("Video recap: /video — mp4: %s", _mp4s or "(chưa có → overlay fallback)")
    else:
        log.info("Video recap: chưa có app/assets/video → overlay fallback")

    # ========================================
    # MVC: Dependency Injection
    # ========================================

    # === REPOSITORIES ===
    challenge_repo = ChallengeRepository()
    script_repo = ScriptRepository()

    # === SERVICES ===
    tts_service = TTSService(
        tts_dir=TTS_DIR,
        audio_dir=data_source.AUDIO_DIR
    )
    judge_service = JudgeService(
        llm=llm,
        model=settings.or_model
    )

    # === SERVICE FACTORY ===
    services = {
        'tts_service': tts_service,
        'judge_service': judge_service,
        'challenge_repository': challenge_repo,
        'script_repository': script_repo,
        'llm': llm,
        'model': settings.or_model,
    }

    def get_service(name: str):
        """Service factory for controllers."""
        return services.get(name)

    # === CONTROLLERS ===
    def session_manager_factory(ws):
        """Factory to create SessionManager instances."""
        return SessionManager(ws=ws, tts_service=tts_service)

    def game_flow_factory(session_manager):
        """Factory to create GameFlowService instances."""
        return GameFlowService(
            session_manager=session_manager,
            judge_service=judge_service,
            challenge_repo=challenge_repo,
            script_repo=script_repo
        )

    websocket_controller = CauVongWebSocketController(
        get_service=get_service,
        session_manager_factory=session_manager_factory,
        game_flow_factory=game_flow_factory
    )

    health_controller = HealthController(
        llm=llm,
        model=settings.or_model,
        live2d_available=live2d_available
    )

    # === REGISTER ROUTES ===
    from games.cau_vong.router import register_routes
    register_routes(
        app,
        websocket_controller=websocket_controller,
        health_controller=health_controller
    )

    register_audio_route(app, TTS_DIR, data_source.AUDIO_DIR)
    return app
