from __future__ import annotations

import re


def summarize_text(text: str, max_sentences: int = 2, max_chars: int = 160) -> str:
    normalized = re.sub(r"\s+", "", text)
    sentences = [
        sentence
        for sentence in re.split(r"(?<=[。！？!?])", normalized)
        if sentence.strip()
    ]
    if not sentences:
        return normalized[:max_chars]
    return "".join(sentences[:max_sentences])[:max_chars]


def first_sentence_of(text: str) -> str:
    return summarize_text(text, max_sentences=1, max_chars=80)


def extract_dialogues(text: str) -> list[str]:
    dialogues = []
    for match in re.findall(r"“([^”]{1,120})”", text):
        cleaned = re.sub(r"\s+", " ", match).strip()
        if cleaned:
            dialogues.append(cleaned)
    return dialogues


def infer_time_of_day(text: str) -> str:
    if any(keyword in text for keyword in ["夜", "晚上", "深夜", "凌晨"]):
        return "night"
    if any(keyword in text for keyword in ["清晨", "早晨", "上午"]):
        return "morning"
    if any(keyword in text for keyword in ["傍晚", "黄昏"]):
        return "evening"
    return "day"


def infer_interior_exterior(text: str) -> str:
    if any(keyword in text for keyword in ["房间", "屋里", "书店", "办公室", "客厅", "厨房"]):
        return "interior"
    if any(keyword in text for keyword in ["街", "路", "巷", "雨中", "门外"]):
        return "exterior"
    return "interior"
