from __future__ import annotations

from typing import Any

from .models import AdaptationPlan, Chapter, Character, ScenePlan, StoryAnalysis
from .text_utils import extract_dialogues


class SceneWriter:
    """Generate screenplay scenes from adaptation plans."""

    def write(
        self,
        chapters: list[Chapter],
        analysis: StoryAnalysis,
        plan: AdaptationPlan,
    ) -> list[dict[str, Any]]:
        chapters_by_id = {chapter.id: chapter for chapter in chapters}
        scenes: list[dict[str, Any]] = []
        for scene_plan in plan.scenes:
            chapter = chapters_by_id[scene_plan.source_chapters[0]]
            scenes.append(write_scene(scene_plan, chapter, analysis.characters))
        return scenes


def write_scene(
    scene_plan: ScenePlan,
    chapter: Chapter,
    characters: list[Character],
) -> dict[str, Any]:
    dialogues = extract_dialogues(chapter.text)
    beats: list[dict[str, str]] = [
        {
            "type": "action",
            "text": rewrite_as_action(chapter.summary, scene_plan.rewrite_strategy),
        }
    ]

    for index, dialogue in enumerate(dialogues[:3]):
        speaker = guess_speaker(chapter.text, dialogue, characters)
        beats.append(
            {
                "type": "dialogue",
                "character_id": speaker.id,
                "text": dialogue,
            }
        )
        if index == 0:
            beats.append(
                {
                    "type": "action",
                    "text": "短暂的沉默改变了场景里的气氛，人物关系开始变得紧张。",
                }
            )

    if len(beats) == 1:
        beats.append(
            {
                "type": "action",
                "text": "人物用动作和停顿承接原文叙事，场景保持可拍摄的外部行为。",
            }
        )

    return {
        "id": scene_plan.id,
        "order": scene_plan.order,
        "source_chapters": scene_plan.source_chapters,
        "heading": {
            "location_id": scene_plan.location_id,
            "time_of_day": scene_plan.time_of_day,
            "interior_exterior": scene_plan.interior_exterior,
        },
        "purpose": scene_plan.purpose,
        "characters": scene_plan.character_ids,
        "beats": beats,
        "transition": "cut_to",
    }


def rewrite_as_action(summary: str, rewrite_strategy: list[str]) -> str:
    if not summary:
        return "场景展开，人物进入关键情境。"
    if "将心理描写转为动作、表情或停顿" in rewrite_strategy:
        return f"画面呈现：人物通过停顿和细微动作带出情绪。{summary}"
    return f"画面呈现：{summary}"


def guess_speaker(text: str, dialogue: str, characters: list[Character]) -> Character:
    dialogue_index = text.find(f"“{dialogue}”")
    context = text[max(0, dialogue_index - 20) : dialogue_index + len(dialogue) + 30]
    for character in characters:
        if character.name in context:
            return character
    return characters[0]
