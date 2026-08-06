"""Composition root Trò 2 — build_app() dựng FastAPI app with MVC architecture.

Tách side-effect ra khỏi import: warmup TTS + tạo client + tempdir chỉ chạy trong build_app()
→ module import được trong test không load Kokoro. Entry point cũ (app/timnang_master.py) là shim
gọi build_app() + run_app().
"""
import os

from core import paths, tts
from core.app_factory import create_app
from core.audio import register_audio_route
from core.config import settings
from core.llm import make_openrouter_client
from core.logging import setup_logging
import timnang_data as data_source

# MVC imports
from games.timnang.repositories import GameObjectRepository, TeamRepository, ScriptRepository
from games.timnang.services import VisionService, GameStateService, ScoringService, BroadcastService, RoundService, TTSService
from games.timnang.controllers import StationWebSocketController, MasterWebSocketController, HealthController

log = setup_logging("timnang")


def build_app():
    TTS_DIR = paths.new_tts_dir("timnang_tts_")
    log.info("TTS temp dir: %s", TTS_DIR)

    llm = make_openrouter_client()
    log.info("Vision/LLM: %s", ("OpenRouter " + settings.or_model) if llm else "TẮT — operator duyệt tay")

    if not tts.tts_available():
        log.warning("kokoro-vietnamese chưa cài — chạy pip install -e ref/Kokoro-Vietnamese[onnx]")
    tts.warmup()  # load model ngay lúc boot (tránh lazy-init block event-loop ở lần say() đầu)

    app = create_app("Tìm Nắng (master)", static_dir=paths.STATIC_DIR)

    # ========================================
    # MVC: Dependency Injection
    # ========================================

    # === REPOSITORIES ===
    object_repo = GameObjectRepository()
    team_repo = TeamRepository()
    script_repo = ScriptRepository()

    # === SERVICES ===
    vision_service = VisionService(llm=llm, model=settings.or_model)
    game_state_service = GameStateService(teams=team_repo.get_all())
    broadcast_service = BroadcastService(game_state=game_state_service, team_repo=team_repo)
    tts_service = TTSService(tts_dir=TTS_DIR, audio_dir=data_source.AUDIO_DIR, broadcast=broadcast_service)
    scoring_service = ScoringService(game_state=game_state_service, script_repo=script_repo)
    round_service = RoundService(
        game_state=game_state_service,
        scoring=scoring_service,
        broadcast=broadcast_service,
        tts=tts_service,
        object_repo=object_repo,
        script_repo=script_repo
    )

    # === SERVICE FACTORY ===
    services = {
        'vision_service': vision_service,
        'game_state_service': game_state_service,
        'scoring_service': scoring_service,
        'broadcast_service': broadcast_service,
        'round_service': round_service,
        'tts_service': tts_service,
        'game_object_repository': object_repo,
        'team_repository': team_repo,
        'script_repository': script_repo,
        'llm': llm,
        'model': settings.or_model,
    }

    def get_service(name: str):
        """Service factory for controllers."""
        return services.get(name)

    # === CONTROLLERS ===
    station_controller = StationWebSocketController(get_service=get_service)
    master_controller = MasterWebSocketController(get_service=get_service)
    health_controller = HealthController(
        llm=llm,
        model=settings.or_model,
        teams=team_repo.get_team_ids(),
        num_objects=object_repo.count()
    )

    # === REGISTER ROUTES ===
    from games.timnang.router import register_routes
    register_routes(
        app,
        station_controller=station_controller,
        master_controller=master_controller,
        health_controller=health_controller,
        team_repo=team_repo
    )

    register_audio_route(app, TTS_DIR, data_source.AUDIO_DIR)

    # Expose core services via app.state for external access if needed
    app.state.game_state = game_state_service
    app.state.round_service = round_service
    app.state.broadcast = broadcast_service

    return app
