from __future__ import annotations

from typing import Any


VALID_FORMATS = {"screenplay", "web_series", "stage_play", "audio_drama"}
VALID_BEAT_TYPES = {
    "action",
    "dialogue",
    "parenthetical",
    "voice_over",
    "sound",
    "transition",
}


def validate_script(script: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = [
        "schema_version",
        "title",
        "format",
        "language",
        "source",
        "logline",
        "synopsis",
        "characters",
        "locations",
        "chapters",
        "scenes",
        "notes",
    ]
    for field in required:
        if field not in script:
            errors.append(f"缺少顶层字段 script.{field}")

    if script.get("format") not in VALID_FORMATS:
        errors.append("script.format 不是合法取值")

    source = script.get("source", {})
    if not isinstance(source, dict) or source.get("type") != "novel":
        errors.append("script.source.type 必须为 novel")

    chapters = script.get("chapters", [])
    if not isinstance(chapters, list) or len(chapters) < 3:
        errors.append("script.chapters 至少需要 3 个章节")

    characters = script.get("characters", [])
    locations = script.get("locations", [])
    scenes = script.get("scenes", [])
    character_ids = collect_ids(characters, "characters", errors)
    location_ids = collect_ids(locations, "locations", errors)
    chapter_ids = collect_ids(chapters, "chapters", errors)

    if not isinstance(scenes, list) or not scenes:
        errors.append("script.scenes 至少需要 1 个场景")
        return errors

    scene_orders: set[int] = set()
    for scene in scenes:
        if not isinstance(scene, dict):
            errors.append("scene 必须是对象")
            continue
        scene_id = scene.get("id", "<unknown>")
        order = scene.get("order")
        if not isinstance(order, int):
            errors.append(f"{scene_id}.order 必须是整数")
        elif order in scene_orders:
            errors.append(f"{scene_id}.order 重复")
        else:
            scene_orders.add(order)

        validate_scene_refs(scene, scene_id, chapter_ids, character_ids, location_ids, errors)
        validate_beats(scene, scene_id, character_ids, errors)

    return errors


def collect_ids(items: Any, label: str, errors: list[str]) -> set[str]:
    ids: set[str] = set()
    if not isinstance(items, list):
        errors.append(f"script.{label} 必须是数组")
        return ids

    for item in items:
        if not isinstance(item, dict):
            errors.append(f"script.{label} 内元素必须是对象")
            continue
        item_id = item.get("id")
        if not isinstance(item_id, str) or not item_id:
            errors.append(f"script.{label} 内元素缺少 id")
            continue
        if item_id in ids:
            errors.append(f"script.{label} 存在重复 id: {item_id}")
        ids.add(item_id)
    return ids


def validate_scene_refs(
    scene: dict[str, Any],
    scene_id: str,
    chapter_ids: set[str],
    character_ids: set[str],
    location_ids: set[str],
    errors: list[str],
) -> None:
    source_chapters = scene.get("source_chapters", [])
    if not source_chapters:
        errors.append(f"{scene_id}.source_chapters 不能为空")
    for chapter_id in source_chapters:
        if chapter_id not in chapter_ids:
            errors.append(f"{scene_id} 引用了未定义章节 {chapter_id}")

    heading = scene.get("heading", {})
    if not isinstance(heading, dict):
        errors.append(f"{scene_id}.heading 必须是对象")
        return

    if heading.get("location_id") not in location_ids:
        errors.append(f"{scene_id}.heading.location_id 引用了未定义地点")
    if not heading.get("time_of_day"):
        errors.append(f"{scene_id}.heading.time_of_day 不能为空")
    if heading.get("interior_exterior") not in {"interior", "exterior"}:
        errors.append(f"{scene_id}.heading.interior_exterior 不是合法取值")

    for character_id in scene.get("characters", []):
        if character_id not in character_ids:
            errors.append(f"{scene_id} 引用了未定义人物 {character_id}")


def validate_beats(
    scene: dict[str, Any],
    scene_id: str,
    character_ids: set[str],
    errors: list[str],
) -> None:
    beats = scene.get("beats", [])
    if not isinstance(beats, list) or not beats:
        errors.append(f"{scene_id}.beats 不能为空")
        return

    has_action = False
    for index, beat in enumerate(beats, start=1):
        if not isinstance(beat, dict):
            errors.append(f"{scene_id}.beats[{index}] 必须是对象")
            continue
        beat_type = beat.get("type")
        if beat_type not in VALID_BEAT_TYPES:
            errors.append(f"{scene_id}.beats[{index}].type 不是合法取值")
        if beat_type == "action":
            has_action = True
        if not beat.get("text"):
            errors.append(f"{scene_id}.beats[{index}].text 不能为空")
        if beat_type in {"dialogue", "parenthetical", "voice_over"}:
            character_id = beat.get("character_id")
            if character_id not in character_ids:
                errors.append(f"{scene_id}.beats[{index}] 引用了未定义人物 {character_id}")

    if not has_action:
        errors.append(f"{scene_id}.beats 至少需要一个 action")
