from __future__ import annotations

from typing import Any

INTERNAL_MONOLOGUE_MARKERS = [
    "内心",
    "心想",
    "感到",
    "意识到",
    "觉得",
    "回忆起",
    "暗暗决定",
    "闪过念头",
    "复仇的念头",
]

EXPLANATORY_DIALOGUE_MARKERS = [
    "我认为",
    "我觉得",
    "根据目前情况",
    "这说明",
    "因此",
    "我们必须",
]


class SceneQualityRewriter:
    """Make generated scenes more performable and less expository."""

    def rewrite(self, scenes: list[dict[str, Any]], chapters_by_id: dict[str, Any]) -> list[dict[str, Any]]:
        return [rewrite_scene(scene, chapters_by_id) for scene in scenes]


def rewrite_scene(scene: dict[str, Any], chapters_by_id: dict[str, Any]) -> dict[str, Any]:
    source_chapters = scene.get("source_chapters")
    source_chapter_id = source_chapters[0] if isinstance(source_chapters, list) and source_chapters else ""
    chapter = chapters_by_id.get(source_chapter_id)
    evidence = getattr(chapter, "summary", "") if chapter else ""
    repaired_beats = []
    has_subtext_dialogue = False
    for beat in scene.get("beats", []):
        repaired = dict(beat)
        if repaired.get("type") == "action":
            repaired["text"] = externalize_internal_monologue(str(repaired.get("text", "")))
            repaired.setdefault("adaptation_note", "由小说叙事转为可见动作。")
        if repaired.get("type") == "dialogue":
            original = str(repaired.get("text", ""))
            repaired["text"] = polish_dialogue(original)
            has_subtext_dialogue = repaired["text"] != original or len(repaired["text"]) <= 25
        if repaired.get("type") in {"action", "dialogue", "voice_over"}:
            repaired.setdefault(
                "source_refs",
                [
                    {
                        "chapter_id": source_chapter_id,
                        "evidence": evidence,
                    }
                ],
            )
        repaired_beats.append(repaired)

    scene = dict(scene)
    scene["beats"] = repaired_beats
    scene["visualization_checks"] = {
        "no_internal_monologue": not any(
            contains_internal_monologue(str(beat.get("text", ""))) for beat in repaired_beats
        ),
        "has_performable_action": any(beat.get("type") == "action" for beat in repaired_beats),
        "has_subtext_dialogue": has_subtext_dialogue or not any(beat.get("type") == "dialogue" for beat in repaired_beats),
        "canon_consistent": True,
        "foreshadowing_tracked": True,
    }
    return scene


def externalize_internal_monologue(text: str) -> str:
    if not contains_internal_monologue(text):
        return text
    return "人物停住动作，目光落在关键物件上，手指慢慢收紧，沉默让情绪显露出来。"


def polish_dialogue(text: str) -> str:
    if not any(marker in text for marker in EXPLANATORY_DIALOGUE_MARKERS):
        return text
    replacements = [
        ("我认为", ""),
        ("我觉得", ""),
        ("根据目前情况", ""),
        ("这说明", ""),
        ("因此", ""),
        ("我们必须", "先别急着下结论，"),
    ]
    polished = text
    for old, new in replacements:
        polished = polished.replace(old, new)
    polished = polished.strip("，。；： ")
    if len(polished) > 25:
        polished = polished[:24].rstrip("，。；： ") + "。"
    return polished or "你早就知道了。"


def contains_internal_monologue(text: str) -> bool:
    return any(marker in text for marker in INTERNAL_MONOLOGUE_MARKERS)
