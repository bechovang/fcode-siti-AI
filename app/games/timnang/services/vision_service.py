"""
Service for AI-based image recognition.
"""

import asyncio
import json
import logging
from typing import Optional, Any

from schemas.timnang import GameObject

log = logging.getLogger("timnang.vision")


class VisionService:
    """Service for AI-based image recognition using multimodal LLM."""

    def __init__(self, llm: Optional[Any] = None, model: Optional[str] = None):
        """
        Initialize vision service.

        Args:
            llm: Optional LLM client with multimodal capabilities
            model: Model name for vision API
        """
        self.llm = llm
        self.model = model

    async def judge_image(self, image_b64: str, obj: GameObject) -> Optional[bool]:
        """
        Judge if image contains the target object using AI vision.

        Args:
            image_b64: Base64-encoded image data (with or without data URL prefix)
            obj: Target GameObject to recognize

        Returns:
            True if object found, False if not found, None if error/no LLM
        """
        if not self.llm:
            return None

        return await asyncio.to_thread(
            self._judge_vision_sync,
            image_b64,
            obj
        )

    def _judge_vision_sync(self, image_b64: str, obj: GameObject) -> Optional[bool]:
        """
        Synchronous vision judgment (runs in thread to avoid blocking event loop).

        Args:
            image_b64: Base64-encoded image data
            obj: Target GameObject to recognize

        Returns:
            True if object found, False if not found, None if error
        """
        data_url = image_b64 if image_b64.startswith("data:") else f"data:image/jpeg;base64,{image_b64}"
        prompt = (
            f"Trong bức ảnh này có {obj.vision_prompt} không? "
            f"Chấp nhận góc nhìn khác nhau, một phần vật cũng OK. "
            f'Chỉ trả JSON hợp lệ: {{"correct": true}} hoặc {{"correct": false}}.'
        )

        try:
            r = self.llm.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ]
                }],
                temperature=0,
            )
            data = json.loads(r.choices[0].message.content.strip())
            return bool(data.get("correct"))
        except Exception as e:
            log.warning("Vision lỗi (%s)", e)
            return None

    def is_available(self) -> bool:
        """Check if vision service is available (has LLM client)."""
        return self.llm is not None
