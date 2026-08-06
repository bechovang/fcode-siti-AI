"""app.schemas — typed domain models + phase enums cho cả 2 trò.

Thay thế bare-dict access (ch['answer'], obj['vision_prompt'], t['order']...) bằng
Pydantic models → IDE/mypy bắt được typo. WS message envelopes (discriminated unions)
sẽ thêm ở Phase 3 cùng validation setup.
"""
