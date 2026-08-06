"""
Service for round orchestration and game flow.
"""

import asyncio
import logging
from typing import Optional

from schemas.timnang import GameObject
from games.timnang.services.game_state_service import GameStateService
from games.timnang.services.scoring_service import ScoringService
from games.timnang.services.broadcast_service import BroadcastService
from games.timnang.services.tts_service import TTSService
from games.timnang.repositories.game_object_repository import GameObjectRepository
from games.timnang.repositories.script_repository import ScriptRepository

log = logging.getLogger("timnang.round")


class RoundService:
    """Service for orchestrating game rounds and flow."""

    def __init__(
        self,
        game_state: GameStateService,
        scoring: ScoringService,
        broadcast: BroadcastService,
        tts: TTSService,
        object_repo: GameObjectRepository,
        script_repo: ScriptRepository,
    ):
        """
        Initialize round service.

        Args:
            game_state: Game state service
            scoring: Scoring service
            broadcast: Broadcast service
            tts: TTS service
            object_repo: Game object repository
            script_repo: Script repository
        """
        self.game_state = game_state
        self.scoring = scoring
        self.broadcast = broadcast
        self.tts = tts
        self.objects = object_repo
        self.scripts = script_repo

    async def start_game(self):
        """Start new game from beginning."""
        await self.game_state.reset()

        # Transition to announce phase
        if not await self.game_state.transition_to_announce():
            log.warning("Failed to transition to ANNOUNCE phase")
            return

        # Stop any playing audio
        await self.broadcast.broadcast_masters({"type": "stop_audio"})

        # Reset all clients
        await self.broadcast.broadcast_all({"type": "reset"})

        # Sync initial scoreboard
        await self.broadcast.sync_scoreboard(self.objects)

        # Play intro
        intro_text = self.scripts.get_intro_text()
        await self.tts.play_or_say("intro", intro_text)

        await asyncio.sleep(0.5)

        # Start first round
        await self.start_round(0)

    async def start_round(self, round_idx: int):
        """Start specific round."""
        obj = self.objects.get_by_index(round_idx)
        if not obj:
            log.error("Object not found for round %d", round_idx)
            return

        # Transition to playing phase
        if not await self.game_state.transition_to_playing(round_idx, obj.id):
            log.warning("Failed to transition to PLAYING phase")
            return

        # Sync scoreboard
        await self.broadcast.sync_scoreboard(self.objects)

        # Broadcast round start to stations
        await self.broadcast.broadcast_stations({
            "type": "round",
            "object": obj.name,
            "vi": obj.vi
        })

        # Play round announcement
        round_text = self.scripts.get_round_text(round_idx, obj)
        audio_key = f"round_{obj.id}"
        await self.tts.play_or_say(audio_key, round_text)

        log.info("Round %d started: %s", round_idx + 1, obj.name)

    async def end_round(self, reason: str):
        """End current round."""
        # Transition to round end phase
        await self.game_state.transition_to_round_end()

        # Generate and play summary
        summary = self._generate_round_summary()
        await self.tts.say(summary)

        # Sync final scoreboard
        await self.broadcast.sync_scoreboard(self.objects)

        await asyncio.sleep(2)

        # Check if more rounds or game over
        if self.game_state.has_more_rounds(self.objects.count()):
            next_round = self.game_state.get_round_index() + 1
            await self.start_round(next_round)
        else:
            await self.game_over()

    def _generate_round_summary(self) -> str:
        """Generate round summary text for TTS."""
        round_idx = self.game_state.get_round_index()
        if round_idx < 0:
            return ""

        # Short summary to reduce lag between rounds
        round_num = self.scripts.num_vi(round_idx + 1)
        return f"Hết vòng {round_num}!"

    async def game_over(self):
        """End game and show final results."""
        await self.game_state.transition_to_game_over()

        ranking = self.game_state.get_ranking()
        if not ranking:
            log.warning("No ranking data available")
            return

        winner = ranking[0]  # Ties keep A/B/C order (stable sort)

        winner_score = self.scripts.num_vi(winner["score"])
        announcement = (
            f"Trò chơi kết thúc! {winner['name']} là nhà vô địch với {winner_score} điểm! "
            f"Chúc mừng các bạn! Cảm ơn tất cả đã tham gia!"
        )

        await self.tts.say(announcement)

        await self.broadcast.broadcast_all({
            "type": "game_over",
            "winner": winner["id"],
            "winner_name": winner["name"],
            "ranking": ranking,
        })

        await self.broadcast.sync_scoreboard(self.objects)
        log.info("Game over. Winner: %s with %d points", winner["name"], winner["score"])

    async def handle_recognition(
        self,
        team_id: str,
        image_b64: str,
        vision_service
    ) -> Optional[dict]:
        """
        Handle recognition request from station.

        Args:
            team_id: Team making recognition request
            image_b64: Base64-encoded image
            vision_service: Vision service for AI recognition

        Returns:
            Result message to send back to station, or None if broadcast
        """
        # Validate phase
        if self.game_state.get_phase().name != "PLAYING":
            return {
                "type": "result",
                "correct": False,
                "msg": "Chờ vòng bắt đầu nhé!"
            }

        # Validate image payload BEFORE calling expensive vision API
        if not image_b64 or not image_b64.startswith("data:image/"):
            return {
                "type": "result",
                "correct": False,
                "msg": "Camera chưa sẵn sàng — thử lại nhé!"
            }

        if len(image_b64) > 5_000_000:
            return {
                "type": "result",
                "correct": False,
                "msg": "Ảnh quá lớn — thử lại nhé!"
            }

        # Check debounce via scoring service
        can_recognize, error_msg = self.scoring.can_recognize(
            team_id,
            self.scripts.get_audio_dir()  # Using as placeholder for debounce config
        )
        if not can_recognize:
            return {"type": "result", "correct": False, "msg": error_msg}

        # Get current object
        obj_id = self.game_state.get_current_object_id()
        obj = self.objects.get_by_id(obj_id) if obj_id else None
        if not obj:
            return {"type": "result", "correct": False, "msg": "Lỗi game — thử lại nhé!"}

        # Call vision API (outside lock to allow parallel)
        correct = await vision_service.judge_image(image_b64, obj)

        if correct is None:
            return {
                "type": "result",
                "correct": None,
                "msg": "AI không chắc — nhờ cô chú duyệt giúp!"
            }

        if not correct:
            return {
                "type": "result",
                "correct": False,
                "msg": "Chưa đúng rồi! Thử lại xem!"
            }

        # Correct → assign order via scoring service
        success, order, points = await self.scoring.assign_order(team_id)
        if not success:
            return {"type": "result", "correct": False, "msg": "Lỗi game — thử lại nhé!"}

        # Generate success message
        team_state = self.game_state.get_team_state(team_id)
        team_name = team_state["name"] if team_state else "Đội"

        result_msg = {
            "type": "result",
            "correct": True,
            "order": order,
            "points": points,
            "msg": f"Đúng rồi! Về {order}! Cộng {points} điểm!"
        }

        # Play correct announcement
        correct_text = self.scripts.get_correct_text(team_name, order)
        audio_key = f"correct_{team_id}_nhat" if order == 1 else f"correct_{team_id}_nhi" if order == 2 else f"correct_{team_id}_ba"
        await self.tts.play_or_say(audio_key, correct_text)

        # Sync scoreboard
        await self.broadcast.sync_scoreboard(self.objects)

        # Check if round complete
        if self.game_state.is_round_complete():
            asyncio.create_task(self.end_round("all_done"))

        return result_msg

    async def operator_force_accept(self, team_id: str):
        """Handle operator force-accept command."""
        success, order, points = await self.scoring.force_accept(team_id)
        if not success:
            log.warning("Force accept failed for team %s", team_id)
            return

        # Generate success message
        team_state = self.game_state.get_team_state(team_id)
        team_name = team_state["name"] if team_state else "Đội"

        # Play correct announcement
        correct_text = self.scripts.get_correct_text(team_name, order)
        audio_key = f"correct_{team_id}_nhat" if order == 1 else f"correct_{team_id}_nhi" if order == 2 else f"correct_{team_id}_ba"
        await self.tts.play_or_say(audio_key, correct_text)

        # Sync scoreboard
        await self.broadcast.sync_scoreboard(self.objects)

        # Check if round complete
        if self.game_state.is_round_complete():
            asyncio.create_task(self.end_round("force_accept"))

        log.info("Operator force accept: team %s → order %d (+%d pts)", team_id, order, points)

    async def operator_add_point(self, team_id: str, delta: int):
        """Handle operator add/subtract points command."""
        success = await self.game_state.update_team_score(team_id, delta)
        if success:
            await self.broadcast.sync_scoreboard(self.objects)
            log.info("Operator add point: team %s %+d", team_id, delta)
        else:
            log.warning("Add point failed for team %s", team_id)

    async def operator_skip_round(self):
        """Handle operator skip round command."""
        await self.end_round("skip")

    async def operator_reset_game(self):
        """Handle operator reset game command."""
        await self.start_game()
