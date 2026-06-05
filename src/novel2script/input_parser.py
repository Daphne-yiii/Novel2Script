from __future__ import annotations

import re

from .errors import PipelineError


class InputParser:
    """Clean raw novel text before chapter segmentation."""

    def parse(self, text: str) -> str:
        cleaned = clean_text(text)
        if not cleaned:
            raise PipelineError("输入文本为空。")
        return cleaned


def clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    lines = [line.strip() for line in text.split("\n")]
    compacted = "\n".join(lines)
    compacted = re.sub(r"\n{3,}", "\n\n", compacted)
    return compacted.strip()
