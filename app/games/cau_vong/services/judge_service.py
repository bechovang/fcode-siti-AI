"""
Service for answer judging (fuzzy matching + LLM).
"""

import json
import logging
from typing import Optional, Tuple, Any

from core import constants as C
from core import llm as llm_module
from rapidfuzz import fuzz
from schemas.cau_vong import Challenge

log = logging.getLogger("koon.judge")


class JudgeService:
    """Service for judging answers with fuzzy matching and optional LLM."""

    def __init__(self, llm: Optional[Any] = None, model: Optional[str] = None):
        """
        Initialize judge service.

        Args:
            llm: Optional LLM client for intelligent judging
            model: Model name for LLM
        """
        self.llm = llm
        self.model = model

    def judge_fuzzy(self, text: str, ch: Challenge) -> bool:
        """
        Fast fuzzy matching for known answer variants.

        Args:
            text: User's answer text
            ch: Challenge with answer and aliases

        Returns:
            True if answer matches fuzzy threshold
        """
        t = (text or "").strip().lower()
        if not t:
            return False
        cands = [ch.answer] + ch.aliases
        return any(fuzz.partial_ratio(t, c) >= C.FUZZY_THRESHOLD for c in cands)

    def _reply_template(self, ch: Challenge, attempts: int) -> str:
        """
        Generate fallback reply template when wrong (no LLM or LLM error).

        Args:
            ch: Current challenge
            attempts: Number of failed attempts

        Returns:
            Encouraging reply text
        """
        hint = ch.hint
        if attempts <= 0:
            return f"Chưa đúng rồi các bạn ơi! Để mình gợi ý nha: {hint}. Các bạn thử lại xem?"
        return f"Gần được rồi! {hint}. Các bạn nghĩ thêm một chút nha, mình tin các bạn làm được!"

    def judge_and_reply(self, text: str, ch: Challenge, attempts: int = 0) -> Tuple[bool, str]:
        """
        Judge answer and generate reply (fuzzy + optional LLM).

        Args:
            text: User's answer text
            ch: Current challenge
            attempts: Number of previous failed attempts

        Returns:
            Tuple of (is_correct, reply_text)
            - is_correct=True, reply='' -> use pre-cache right audio
            - is_correct=True, reply!='' -> dynamic TTS confirmation
            - is_correct=False -> reply is conversation response
        """
        # Fuzzy FIRST: trust aliases for known variants - prevent LLM mistakes on obvious correct answers
        if self.judge_fuzzy(text, ch):
            return True, ""

        if self.llm:
            return self._llm_judge_and_reply(text, ch, attempts)

        # Fuzzy already checked at top -> reaching here is definitely WRONG
        return False, self._reply_template(ch, attempts)

    def _llm_judge_and_reply(self, text: str, ch: Challenge, attempts: int) -> Tuple[bool, str]:
        """
        Use LLM to judge answer and generate contextual reply.

        Args:
            text: User's answer text
            ch: Current challenge
            attempts: Number of previous failed attempts

        Returns:
            Tuple of (is_correct, reply_text)
        """
        sysp = (
            "Bạn là KOON, nhân vật AI dẫn trò chơi đố vui cho trẻ em tiếng Việt, đang chơi cùng các bạn nhỏ. Nhiệm vụ:\n"
            "1. Chấm xem câu bé nói có THỎA MÃN câu đố không. CÂU ĐỐ CÓ THỂ CÓ NHIỀU ĐÁP ÁN HỢP LÝ — bất kỳ đáp án nào "
            "đúng với mô tả đều ĐÚNG, không chỉ đáp án gợi ý. Ví dụ \"cái gì có 4 chân nhưng không biết đi\" thì "
            "\"cái bàn\", \"ghế\", \"tủ\", \"giường\" đều ĐÚNG. Đáp án sai logic (không thỏa mãn mô tả) mới là SAI. "
            "Chấp nhận sai chính tả, không dấu, từ đồng nghĩa, từ lễ phép (dạ/ạ/em).\n"
            "Lưu ý: đáp án gợi ý là đáp án chính/cổ điển của câu đố. Một đáp án KHÁC chỉ ĐÚNG khi nó RÕ RÀNG thỏa mãn "
            "toàn bộ các đặc điểm trong mô tả (không chỉ cùng nhóm/tương tự). Nếu chỉ hơi giống hoặc thiếu một đặc điểm "
            "quan trọng → SAI. Ví dụ \"chúa tể rừng xanh\" → sư tử ĐÚNG, còn hổ/beo là SAI (không phải chúa tể rừng xanh).\n"
            "2. Nếu ĐÚNG: sinh 1-2 câu khen ngợi + XÁC NHẬN đáp án bé nói (đúng sự thật, động theo câu bé nói). "
            "Ví dụ bé nói \"ghế\": \"Đúng rồi! Ghế cũng có bốn chân và không biết đi! Các bạn giỏi quá!\". "
            "Không cần khớp đáp án gợi ý.\n"
            "3. Nếu SAI: sinh 1-2 câu đáp lại hội thoại, lễ phép, khích lệ thử lại — dựa câu bé nói và gợi ý. "
            "KHÔNG tiết lộ đáp án. TUYỆT ĐỐI KHÔNG bịa ra lý do sai sự thật để bác bỏ (ví dụ không được nói "
            "\"ghế không có chân\" khi ghế có chân). Nếu không chắc bé nói đúng hay sai, hãy cho là SAI rồi gợi ý thêm.\n"
            "Luôn an toàn, vui vẻ, phù hợp trẻ em; không thô tục, không nhắc chuyện người lớn.\n"
            'Chỉ trả JSON hợp lệ: {"correct": true|false, "reply": "..."}.'
        )
        usrp = (f"Câu đố: \"{ch.question_text}\". Đáp án gợi ý (chỉ tham khảo): \"{ch.answer}\". "
                f"Gợi ý: \"{ch.hint}\". Số lần bé đã sai trước đó: {attempts}. Câu bé vừa nói: \"{text}\".")

        try:
            r = self.llm.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": sysp}, {"role": "user", "content": usrp}],
                temperature=0.3,
            )
            data = json.loads(r.choices[0].message.content.strip())
            correct = bool(data.get("correct"))
            reply = (data.get("reply") or "").strip()
            if correct:
                return True, reply or "Đúng rồi! Các bạn giỏi quá!"
            return False, reply or self._reply_template(ch, attempts)
        except Exception as e:
            log.warning("LLM judge_and_reply lỗi (%s) -> template", e)
            # Fuzzy already checked at top -> reaching here is definitely WRONG
            return False, self._reply_template(ch, attempts)
