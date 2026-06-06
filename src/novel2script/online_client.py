from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any

from .errors import PipelineError
from .input_parser import clean_text
from .validator import validate_script


DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_MODEL = "qwen3.6-plus"


def generate_script_with_llm(source: str, title: str, script_format: str) -> dict[str, Any]:
    config = LLMConfig.from_env()
    cleaned = clean_text(source)
    if not cleaned:
        raise PipelineError("输入文本为空。")

    payload = {
        "model": config.model,
        "messages": build_messages(cleaned, title, script_format),
        "temperature": 0.4,
        "response_format": {"type": "json_object"},
    }
    response = post_chat_completion(config, payload)
    content = extract_message_content(response)
    script = parse_script_json(content)
    script = repair_script(script, cleaned, title, script_format)
    errors = validate_script(script)
    if errors:
        raise PipelineError("在线模型返回结果未通过 Schema 校验：" + "；".join(errors))
    return script


class LLMConfig:
    def __init__(self, api_key: str, base_url: str, model: str, provider: str) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.provider = provider

    @classmethod
    def from_env(cls) -> "LLMConfig":
        api_key = os.getenv("LLM_API_KEY", "").strip()
        if not api_key:
            raise PipelineError("缺少 LLM_API_KEY，请先在终端配置国产模型 API Key。")
        return cls(
            api_key=api_key,
            base_url=os.getenv("LLM_BASE_URL", DEFAULT_BASE_URL).strip() or DEFAULT_BASE_URL,
            model=os.getenv("LLM_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL,
            provider=os.getenv("LLM_PROVIDER", "qwen").strip() or "qwen",
        )


def build_messages(source: str, title: str, script_format: str) -> list[dict[str, str]]:
    system_prompt = (
        "你是一位资深小说改编剧本编辑和结构化数据工程师。"
        "请把中文小说改编为严格 JSON 对象，根字段必须是 script。"
        "必须严格使用用户给出的字段名，不要自创字段名。"
        "不要输出 Markdown，不要输出解释。"
    )
    user_prompt = f"""
请根据以下约束生成剧本 JSON：

1. 输出必须是合法 JSON，根对象形如 {{"script": {{...}}}}。
2. script 必须包含 schema_version、title、format、language、source、logline、synopsis、characters、locations、chapters、scenes、notes。
3. script.source 必须是 {{"type":"novel","chapter_count":章节数量}}，type 必须等于 novel。
4. characters、locations、chapters、scenes 的 id 必须唯一。
5. chapters 中每个对象必须包含 id、title、order、summary。order 必须是数字，不要用字符串。
6. scenes 中每个对象必须包含 id、order、source_chapters、heading、purpose、characters、beats、transition。
7. scene.id 必须使用 scene_001 这种格式，不要使用 scn_001。
8. scene.order 必须是数字。
9. scene.source_chapters 必须是数组，例如 ["chapter_001"]，并引用 chapters.id。
10. scene.heading 必须是对象，且包含 location_id、time_of_day、interior_exterior。
11. scene.beats 必须是数组；每个 beat 必须包含 type 和 text 字段。不要使用 content、description、line、dialogue_text 替代 text。
12. 每个 scene 至少包含一个 action beat。
13. dialogue、parenthetical、voice_over 如包含 character_id，必须引用已定义人物。
14. 心理描写要优先转为动作、表情、沉默、对白或场景调度。
15. 大段背景说明要拆成可视化信息，必要时使用 voice_over。
16. 不要仿写受版权保护作品，不要生成违法违规、不利于未成年人的内容。

剧本标题：{title or "未命名剧本"}
剧本类型：{script_format}
输出语言：zh-CN

小说正文：
{source}
""".strip()
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def post_chat_completion(config: LLMConfig, payload: dict[str, Any]) -> dict[str, Any]:
    url = f"{config.base_url}/chat/completions"
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise PipelineError(f"在线模型请求失败：HTTP {exc.code} {detail}") from exc
    except urllib.error.URLError as exc:
        raise PipelineError(f"在线模型连接失败：{exc.reason}") from exc
    return json.loads(body)


def extract_message_content(response: dict[str, Any]) -> str:
    try:
        content = response["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise PipelineError("在线模型响应格式异常，未找到 choices[0].message.content。") from exc
    if isinstance(content, list):
        return "".join(part.get("text", "") for part in content if isinstance(part, dict))
    return str(content)


def parse_script_json(content: str) -> dict[str, Any]:
    cleaned = strip_code_fences(content.strip())
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise PipelineError(f"在线模型没有返回合法 JSON：{exc}") from exc

    if not isinstance(data, dict) or "script" not in data:
        raise PipelineError("在线模型返回 JSON 缺少根字段 script。")
    script = data["script"]
    if not isinstance(script, dict):
        raise PipelineError("在线模型返回的 script 必须是对象。")
    return script


def strip_code_fences(text: str) -> str:
    match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", text, flags=re.DOTALL)
    return match.group(1) if match else text


def repair_script(
    script: dict[str, Any],
    source: str,
    title: str,
    script_format: str,
) -> dict[str, Any]:
    script = dict(script)
    chapters = normalize_list(script.get("chapters"))
    characters = normalize_list(script.get("characters"))
    locations = normalize_list(script.get("locations"))
    scenes = normalize_list(script.get("scenes"))

    if len(chapters) < 3:
        chapters = fallback_chapters(source)
    chapters = [repair_chapter(chapter, index) for index, chapter in enumerate(chapters, start=1)]

    if not characters:
        characters = [{"id": "char_001", "name": "未知人物", "role": "protagonist", "description": "待细化。", "traits": ["待细化"]}]
    characters = [repair_character(character, index) for index, character in enumerate(characters, start=1)]

    if not locations:
        locations = [{"id": "loc_001", "name": "主要场景", "description": "待细化的主要场景。"}]
    locations = [repair_location(location, index) for index, location in enumerate(locations, start=1)]

    if not scenes:
        scenes = fallback_scenes(chapters, characters, locations)
    else:
        scenes = [
            repair_scene(scene, index, chapters, characters, locations)
            for index, scene in enumerate(scenes, start=1)
        ]

    script["schema_version"] = str(script.get("schema_version") or "1.0")
    script["title"] = str(script.get("title") or title or "未命名剧本")
    script["format"] = script_format if script_format in {"screenplay", "web_series", "stage_play", "audio_drama"} else "screenplay"
    script["language"] = str(script.get("language") or "zh-CN")
    script["source"] = {
        "type": "novel",
        "chapter_count": len(chapters),
    }
    script["logline"] = str(script.get("logline") or "人物在连续事件中追寻真相，并面对逐渐升级的冲突。")
    script["synopsis"] = str(script.get("synopsis") or " ".join(chapter["summary"] for chapter in chapters))
    script["characters"] = characters
    script["locations"] = locations
    script["chapters"] = chapters
    script["scenes"] = scenes
    script["notes"] = normalize_list(script.get("notes"))
    return script


def normalize_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def repair_chapter(chapter: Any, index: int) -> dict[str, Any]:
    data = chapter if isinstance(chapter, dict) else {}
    return {
        "id": normalize_id(data.get("id"), "chapter", index),
        "title": str(data.get("title") or f"第{index}章"),
        "order": to_int(data.get("order"), index),
        "summary": str(data.get("summary") or data.get("synopsis") or data.get("content") or "待补充章节摘要。"),
    }


def repair_character(character: Any, index: int) -> dict[str, Any]:
    data = character if isinstance(character, dict) else {}
    return {
        "id": normalize_id(data.get("id"), "char", index),
        "name": str(data.get("name") or data.get("character") or "未知人物"),
        "role": str(data.get("role") or ("protagonist" if index == 1 else "supporting")),
        "description": str(data.get("description") or data.get("summary") or "待细化。"),
        "traits": normalize_string_list(data.get("traits")) or ["待细化"],
    }


def repair_location(location: Any, index: int) -> dict[str, Any]:
    data = location if isinstance(location, dict) else {}
    return {
        "id": normalize_id(data.get("id"), "loc", index),
        "name": str(data.get("name") or data.get("location") or "主要场景"),
        "description": str(data.get("description") or data.get("summary") or "待细化的场景空间。"),
    }


def repair_scene(
    scene: Any,
    index: int,
    chapters: list[dict[str, Any]],
    characters: list[dict[str, Any]],
    locations: list[dict[str, Any]],
) -> dict[str, Any]:
    data = scene if isinstance(scene, dict) else {}
    chapter_id = chapters[min(index - 1, len(chapters) - 1)]["id"]
    location_id = locations[0]["id"]
    character_ids = [character["id"] for character in characters[:3]]
    heading = data.get("heading") if isinstance(data.get("heading"), dict) else {}
    beats = repair_beats(data.get("beats"), character_ids)
    return {
        "id": normalize_id(data.get("id"), "scene", index),
        "order": to_int(data.get("order"), index),
        "source_chapters": normalize_ref_list(data.get("source_chapters"), {chapter["id"] for chapter in chapters}) or [chapter_id],
        "heading": {
            "location_id": heading.get("location_id") if heading.get("location_id") in {location["id"] for location in locations} else location_id,
            "time_of_day": str(heading.get("time_of_day") or data.get("time_of_day") or "day"),
            "interior_exterior": normalize_interior_exterior(heading.get("interior_exterior") or data.get("interior_exterior")),
        },
        "purpose": str(data.get("purpose") or data.get("function") or "推进情节和人物关系。"),
        "characters": normalize_ref_list(data.get("characters"), set(character_ids)) or character_ids,
        "beats": beats,
        "transition": str(data.get("transition") or "cut_to"),
    }


def repair_beats(value: Any, character_ids: list[str]) -> list[dict[str, Any]]:
    raw_beats = value if isinstance(value, list) else []
    beats: list[dict[str, Any]] = []
    for beat in raw_beats:
        if not isinstance(beat, dict):
            continue
        beat_type = str(beat.get("type") or "action")
        if beat_type not in {"action", "dialogue", "parenthetical", "voice_over", "sound", "transition"}:
            beat_type = "action"
        text = first_text_value(beat)
        if not text:
            text = "人物通过动作和停顿推进场景。"
        repaired: dict[str, Any] = {"type": beat_type, "text": text}
        if beat_type in {"dialogue", "parenthetical", "voice_over"}:
            repaired["character_id"] = beat.get("character_id") if beat.get("character_id") in character_ids else character_ids[0]
        beats.append(repaired)
    if not beats:
        beats.append({"type": "action", "text": "场景展开，人物进入关键情境。"})
    if not any(beat["type"] == "action" for beat in beats):
        beats.insert(0, {"type": "action", "text": "场景展开，人物进入关键情境。"})
    return beats


def first_text_value(data: dict[str, Any]) -> str:
    for key in ["text", "content", "description", "line", "dialogue_text", "action"]:
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def normalize_id(value: Any, prefix: str, index: int) -> str:
    text = str(value or "")
    if re.fullmatch(rf"{re.escape(prefix)}_\d{{3}}", text):
        return text
    if prefix == "scene" and re.fullmatch(r"scn_\d{3}", text):
        return "scene_" + text.rsplit("_", 1)[1]
    return f"{prefix}_{index:03d}"


def to_int(value: Any, default: int) -> int:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        match = re.search(r"\d+", value)
        if match:
            return int(match.group())
    return default


def normalize_ref_list(value: Any, allowed: set[str]) -> list[str]:
    items = value if isinstance(value, list) else []
    return [item for item in items if isinstance(item, str) and item in allowed]


def normalize_string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def normalize_interior_exterior(value: Any) -> str:
    text = str(value or "").lower()
    if text in {"exterior", "ext", "外景", "室外"}:
        return "exterior"
    return "interior"


def fallback_chapters(source: str) -> list[dict[str, Any]]:
    parts = [part.strip() for part in re.split(r"\n\s*\n", source) if part.strip()]
    if len(parts) < 3:
        parts = [source, source, source]
    return [
        {
            "id": f"chapter_{index:03d}",
            "title": f"临时章节 {index}",
            "order": index,
            "summary": part[:120] or "待补充章节摘要。",
        }
        for index, part in enumerate(parts[:3], start=1)
    ]


def fallback_scenes(
    chapters: list[dict[str, Any]],
    characters: list[dict[str, Any]],
    locations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        repair_scene({}, index, chapters, characters, locations)
        for index, _chapter in enumerate(chapters, start=1)
    ]
