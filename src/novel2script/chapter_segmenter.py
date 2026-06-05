from __future__ import annotations

import re

from .models import Chapter
from .text_utils import first_sentence_of, summarize_text


class ChapterSegmenter:
    """Split cleaned novel text into traceable chapter objects."""

    def segment(self, text: str) -> list[Chapter]:
        raw_chapters = find_titled_chapters(text)
        if len(raw_chapters) < 3:
            raw_chapters = split_by_separators(text)
        if len(raw_chapters) < 3:
            raw_chapters = semantic_chunk(text, target_count=3)

        chapters: list[Chapter] = []
        for index, (title, body) in enumerate(raw_chapters, start=1):
            safe_title = title or f"临时章节 {index}"
            chapters.append(
                Chapter(
                    id=f"chapter_{index:03d}",
                    title=safe_title,
                    order=index,
                    text=body,
                    summary=summarize_text(body, max_sentences=2),
                )
            )
        return chapters


def find_titled_chapters(text: str) -> list[tuple[str, str]]:
    chapter_pattern = re.compile(
        r"(?m)^(第[一二三四五六七八九十百千万零〇两\d]+[章节回部卷][^\n]*|"
        r"Chapter\s+\d+[^\n]*|\d+[\.、]\s*[^\n]{1,40})$",
        re.IGNORECASE,
    )
    matches = list(chapter_pattern.finditer(text))
    raw_chapters: list[tuple[str, str]] = []
    if len(matches) < 3:
        return raw_chapters

    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        title = match.group(1).strip()
        body = text[start:end].strip()
        if body:
            raw_chapters.append((title, body))
    return raw_chapters


def split_by_separators(text: str) -> list[tuple[str, str]]:
    parts = [
        part.strip()
        for part in re.split(r"(?m)^\s*(?:-{3,}|\*{3,}|={3,})\s*$", text)
        if part.strip()
    ]
    if len(parts) < 3:
        return []
    return [(f"临时章节 {index}", part) for index, part in enumerate(parts, start=1)]


def semantic_chunk(text: str, target_count: int) -> list[tuple[str, str]]:
    paragraphs = [paragraph.strip() for paragraph in re.split(r"\n\s*\n", text) if paragraph.strip()]
    if len(paragraphs) < target_count:
        return []

    chunk_size = max(1, len(paragraphs) // target_count)
    chunks: list[list[str]] = []
    for index in range(target_count):
        start = index * chunk_size
        end = (index + 1) * chunk_size if index < target_count - 1 else len(paragraphs)
        chunk = paragraphs[start:end]
        if chunk:
            chunks.append(chunk)

    return [(f"临时章节 {index}", "\n\n".join(chunk)) for index, chunk in enumerate(chunks, start=1)]


def infer_title(chapters: list[Chapter]) -> str:
    first_title = chapters[0].title
    if first_title.startswith("第") or first_title.startswith("临时章节"):
        first_sentence = first_sentence_of(chapters[0].text)
        return (first_sentence[:12] or "未命名剧本").strip("，。！？；：")
    return first_title[:30]
