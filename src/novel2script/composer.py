from __future__ import annotations

from typing import Any

from .chapter_segmenter import infer_title
from .models import Chapter, Character, Location, StoryAnalysis


class YAMLComposer:
    """Compose stable script dictionaries before YAML serialization."""

    def compose(
        self,
        chapters: list[Chapter],
        analysis: StoryAnalysis,
        scenes: list[dict[str, Any]],
        *,
        title: str | None,
        script_format: str,
    ) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "title": title or infer_title(chapters),
            "format": script_format,
            "language": "zh-CN",
            "source": {
                "type": "novel",
                "chapter_count": len(chapters),
            },
            "logline": build_logline(analysis),
            "synopsis": build_synopsis(chapters),
            "story_bible": analysis.story_bible,
            "foreshadowing_ledger": analysis.foreshadowing_ledger,
            "canon_facts": analysis.canon_facts,
            "rhythm_plan": analysis.rhythm_plan,
            "characters": [character_to_dict(character) for character in analysis.characters],
            "locations": [location_to_dict(location) for location in analysis.locations],
            "chapters": [chapter_to_dict(chapter) for chapter in chapters],
            "scenes": scenes,
            "coverage_report": analysis.coverage_report,
            "notes": [
                "当前版本使用本地规则引擎生成剧本初稿，适合作为 AI 或人工二次打磨的结构化底稿。",
                f"故事基调：{analysis.tone}。",
            ],
        }


def build_logline(analysis: StoryAnalysis) -> str:
    protagonist = analysis.characters[0].name if analysis.characters else "主角"
    conflict = analysis.conflicts[0] if analysis.conflicts else "逐渐升级的冲突"
    return f"{protagonist}在连续事件中追寻真相，并面对{conflict}"


def build_synopsis(chapters: list[Chapter]) -> str:
    summaries = [chapter.summary for chapter in chapters if chapter.summary]
    return " ".join(summaries)


def chapter_to_dict(chapter: Chapter) -> dict[str, Any]:
    return {
        "id": chapter.id,
        "title": chapter.title,
        "order": chapter.order,
        "summary": chapter.summary,
    }


def character_to_dict(character: Character) -> dict[str, Any]:
    return {
        "id": character.id,
        "name": character.name,
        "role": character.role,
        "description": character.description,
        "traits": character.traits,
        "speech_style": character.speech_style,
    }


def location_to_dict(location: Location) -> dict[str, Any]:
    return {
        "id": location.id,
        "name": location.name,
        "description": location.description,
    }
