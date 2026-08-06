"""
Service for game flow orchestration (7 challenges + rainbow + recap).
"""

import asyncio
import logging
import os
from typing import Optional, Tuple

from schemas.cau_vong import Game1Phase, Challenge
from games.cau_vong.services.session_manager import SessionManager
from games.cau_vong.services.judge_service import JudgeService
from games.cau_vong.repositories.challenge_repository import ChallengeRepository
from games.cau_vong.repositories.script_repository import ScriptRepository

log = logging.getLogger("koon.flow")


class GameFlowService:
    """Service for orchestrating complete game flow."""

    def __init__(
        self,
        session_manager: SessionManager,
        judge_service: JudgeService,
        challenge_repo: ChallengeRepository,
        script_repo: ScriptRepository,
    ):
        """
        Initialize game flow service.

        Args:
            session_manager: Session management service
            judge_service: Answer judging service
            challenge_repo: Challenge data repository
            script_repo: Script and narrative repository
        """
        self.session = session_manager
        self.judge = judge_service
        self.challenges = challenge_repo
        self.scripts = script_repo

    def find_recap_video(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Find recap video file.

        Returns:
            Tuple of (file_path, url) or (None, None)
        """
        video_dir = self.scripts.get_video_dir()
        recap_video = self.scripts.get_recap_video_path()

        if os.path.isfile(recap_video):
            return recap_video, "/video/recap.mp4"

        if os.path.isdir(video_dir):
            for f in sorted(os.listdir(video_dir)):
                if f.lower().endswith(".mp4") and os.path.isfile(os.path.join(video_dir, f)):
                    return os.path.join(video_dir, f), f"/video/{f}"

        return None, None

    async def run_full_game(self):
        """
        Run complete game flow (intro + 7 challenges + rainbow + recap + goodbye).

        Raises:
            asyncio.CancelledError: If game is cancelled
        """
        try:
            await self._run_intro()
            await self._run_challenges()
            await self._run_rainbow()
            await self._run_recap()
            await self._run_done()

            log.info("Hoàn thành show.")

        except asyncio.CancelledError:
            raise
        except Exception as e:
            log.exception("run_flow lỗi (%s) — gửi recovery, không crash show", e)
            try:
                await self.session.send_message({
                    "type": "error",
                    "msg": "Úi, có trục trặc nhỏ. Nhờ cô chú bấm Chạy lại nhé!"
                })
            except Exception:
                pass

    async def _run_intro(self):
        """Run intro sequence with audio narration."""
        self.session.state.phase = Game1Phase.INTRO
        await self.session.send_state(self.challenges.count())

        intro_keys = self.scripts.get_intro_keys()
        intro_lines = self.scripts.get_intro_lines()

        for i, line in enumerate(intro_lines):
            if self.session.has_operator_command():
                op = self.session.get_and_clear_operator_command()
                if op == "skip":
                    break

            await self.session.play_or_say(intro_keys[i], line)

    async def _run_challenges(self):
        """Run 7 challenge sequence."""
        all_challenges = self.challenges.get_all()

        for i, ch in enumerate(all_challenges):
            self.session.state.challenge_index = i
            success = await self._run_challenge(ch, i)
            if not success:
                break  # Skip pressed

    async def _run_challenge(self, ch: Challenge, idx: int) -> bool:
        """
        Run single challenge loop.

        Args:
            ch: Challenge to run
            idx: Challenge index

        Returns:
            True if challenge completed, False if skipped
        """
        self.session.state.phase = Game1Phase.ASK
        await self.session.send_state(self.challenges.count())

        await self.session.send_message({
            "type": "show_question",
            "text": ch.question_text,
            "color": ch.color,
            "hex": ch.hex,
        })

        attempts = 0
        read_q = True  # Read question first time (and on replay)

        while True:  # Retry loop when wrong
            if self.session.has_operator_command():
                op = self.session.get_and_clear_operator_command()
                if op == "skip":
                    return False

            # KOON reads question (only first time or on replay - NOT repeat when wrong)
            if read_q or self.session.has_operator_command():
                op = self.session.get_and_clear_operator_command()
                if op == "replay":
                    pass  # Clear and continue
                if op == "skip":
                    return False

                await self.session.play_or_say(
                    ch.q,
                    f"Câu hỏi thứ {ch.n} màu {ch.color.lower()}: {ch.question_text}",
                )
                read_q = False

                if self.session.has_operator_command():
                    op = self.session.get_and_clear_operator_command()
                    if op == "skip":
                        return False

            # Wait for child's answer
            self.session.state.phase = Game1Phase.AWAIT
            await self.session.send_state(self.challenges.count())
            await self.session.send_message({"type": "await_answer"})

            if self.session.has_operator_command():
                op = self.session.get_and_clear_operator_command()
                if op in ("force_correct", "skip"):
                    self.session.answer_ready_event.set()  # Op pressed before wait -> exit immediately

            await self.session.wait_for_answer()

            if self.session.has_operator_command():
                op = self.session.get_and_clear_operator_command()
                if op == "skip":
                    return False

            ans = self.session.get_answer()
            op = self.session.get_and_clear_operator_command()

            if op == "force_correct":
                correct = True
                reply = ""
            else:
                correct, reply = self.judge.judge_and_reply(ans, ch, attempts)

            attempts += 1
            log.info("Thử thách %d (lần %d): '%s' -> %s", ch.n, attempts, ans, "ĐÚNG" if correct else "SAI")

            self.session.state.phase = Game1Phase.FEEDBACK
            await self.session.send_state(self.challenges.count())

            if correct:
                if reply:
                    # Alternative valid answer -> LLM dynamic confirmation
                    await self.session.say_text(reply)
                else:
                    # Expected answer -> pre-cache right (fast)
                    await self.session.play_or_say(
                        ch.right,
                        f"Chính xác! Đáp án là {ch.answer}. Các bạn giỏi quá! Mảnh màu {ch.color.lower()} đã được tìm thấy!",
                    )
                self.session.state.unlocked_colors.append(ch.hex)
                await self.session.send_message({"type": "unlock_color", "hex": ch.hex})
                return True  # Challenge complete
            else:
                # Conversational response - DON'T re-read question
                await self.session.say_text(reply)

    async def _run_rainbow(self):
        """Run rainbow animation phase."""
        self.session.state.phase = Game1Phase.RAINBOW
        await self.session.send_state(self.challenges.count())
        await self.session.send_message({"type": "rainbow"})
        await asyncio.sleep(4)

    async def _run_recap(self):
        """Run recap video phase."""
        self.session.state.phase = Game1Phase.RECAP
        await self.session.send_state(self.challenges.count())

        recap_key = self.scripts.get_recap_key()
        outro_recap = self.scripts.get_outro_recap()
        magic_line = self.scripts.get_magic_line()

        await self.session.play_or_say(recap_key, outro_recap)
        await self.session.send_message({"type": "magic_reveal"})  # KOON flies + magic reveal -> video transition
        await self.session.say_text(magic_line)
        await asyncio.sleep(0.3)

        # Play recap video if available, else overlay animation fallback
        vpath, vurl = self.find_recap_video()
        if vurl:
            log.info("Recap video phát: %s", vurl)
            await self.session.send_message({"type": "play_video", "url": vurl})
        else:
            await self.session.send_message({"type": "show_recap_overlay"})

        await self.session.wait_for_video_end()

    async def _run_done(self):
        """Run goodbye phase."""
        self.session.state.phase = Game1Phase.DONE
        await self.session.send_state(self.challenges.count())

        goodbye_key = self.scripts.get_goodbye_key()
        outro_goodbye = self.scripts.get_outro_goodbye()

        await self.session.play_or_say(goodbye_key, outro_goodbye)
