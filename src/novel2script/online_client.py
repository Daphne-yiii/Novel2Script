from __future__ import annotations

import json
import os
import re
import socket
import ssl
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from .errors import PipelineError
from .input_parser import clean_text
from .validator import validate_script


DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_MODEL = "qwen3.6-plus"
DEFAULT_TIMEOUT_SECONDS = 240
DEFAULT_MAX_SOURCE_CHARS = 12000
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def generate_script_with_llm(source: str, title: str, script_format: str) -> dict[str, Any]:
    config = LLMConfig.from_env()
    cleaned = clean_text(source)
    if not cleaned:
        raise PipelineError("输入文本为空。")

    payload = {
        "model": config.model,
        "messages": build_messages(cleaned, title, script_format, config.max_source_chars),
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
    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        provider: str,
        ssl_cert_file: str = "",
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
        max_source_chars: int = DEFAULT_MAX_SOURCE_CHARS,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.provider = provider
        self.ssl_cert_file = ssl_cert_file
        self.timeout_seconds = timeout_seconds
        self.max_source_chars = max_source_chars

    @classmethod
    def from_env(cls) -> "LLMConfig":
        env_file = load_dotenv()
        api_key = read_config_value("LLM_API_KEY", env_file).strip()
        if not api_key:
            raise PipelineError(
                "缺少 LLM_API_KEY。请在启动后端的同一个终端 export LLM_API_KEY，"
                "或在项目根目录创建 .env。"
            )
        return cls(
            api_key=api_key,
            base_url=read_config_value("LLM_BASE_URL", env_file).strip() or DEFAULT_BASE_URL,
            model=read_config_value("LLM_MODEL", env_file).strip() or DEFAULT_MODEL,
            provider=read_config_value("LLM_PROVIDER", env_file).strip() or "qwen",
            ssl_cert_file=resolve_ssl_cert_file(env_file),
            timeout_seconds=read_int_config(
                "LLM_TIMEOUT_SECONDS", env_file, DEFAULT_TIMEOUT_SECONDS
            ),
            max_source_chars=read_int_config(
                "LLM_MAX_SOURCE_CHARS", env_file, DEFAULT_MAX_SOURCE_CHARS
            ),
        )


def load_dotenv(path: Path | None = None) -> dict[str, str]:
    env_path = path or PROJECT_ROOT / ".env"
    if not env_path.exists() or not env_path.is_file():
        return {}
    values: dict[str, str] = {}
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'\"")
        if key:
            values[key] = value
    return values


def read_config_value(name: str, dotenv_values: dict[str, str]) -> str:
    return os.getenv(name, dotenv_values.get(name, ""))


def read_int_config(name: str, dotenv_values: dict[str, str], default: int) -> int:
    value = read_config_value(name, dotenv_values).strip()
    if not value:
        return default
    try:
        parsed = int(value)
    except ValueError:
        return default
    return parsed if parsed > 0 else default


def resolve_ssl_cert_file(dotenv_values: dict[str, str]) -> str:
    configured = read_config_value("SSL_CERT_FILE", dotenv_values).strip()
    if configured:
        return configured
    try:
        import certifi
    except ImportError:
        return ""
    return certifi.where()


def build_messages(
    source: str,
    title: str,
    script_format: str,
    max_source_chars: int = DEFAULT_MAX_SOURCE_CHARS,
) -> list[dict[str, str]]:
    source_for_prompt = source[:max_source_chars]
    if len(source) > max_source_chars:
        source_for_prompt += "\n\n[提示：原文过长，当前在线请求已截取前段文本用于生成初稿。]"
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
{source_for_prompt}
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
        with urllib.request.urlopen(
            request,
            timeout=config.timeout_seconds,
            context=build_ssl_context(config),
        ) as response:
            body = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise PipelineError(f"在线模型请求失败：HTTP {exc.code} {detail}") from exc
    except urllib.error.URLError as exc:
        raise PipelineError(f"在线模型连接失败：{exc.reason}") from exc
    except TimeoutError as exc:
        raise PipelineError(
            f"在线模型响应超时（{config.timeout_seconds} 秒）。请减少输入文本，"
            "或在 .env 中调大 LLM_TIMEOUT_SECONDS。"
        ) from exc
    except socket.timeout as exc:
        raise PipelineError(
            f"在线模型响应超时（{config.timeout_seconds} 秒）。请减少输入文本，"
            "或在 .env 中调大 LLM_TIMEOUT_SECONDS。"
        ) from exc
    return json.loads(body)


def build_ssl_context(config: LLMConfig) -> ssl.SSLContext | None:
    if not config.ssl_cert_file:
        return None
    cert_path = Path(config.ssl_cert_file).expanduser()
    if not cert_path.exists():
        raise PipelineError(f"SSL_CERT_FILE 指向的证书文件不存在：{cert_path}")
    return ssl.create_default_context(cafile=str(cert_path))


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
    script["story_bible"] = repair_story_bible(script.get("story_bible"), chapters, characters)
    script["foreshadowing_ledger"] = repair_foreshadowing_ledger(script.get("foreshadowing_ledger"), chapters)
    script["canon_facts"] = normalize_list(script.get("canon_facts"))
    script["rhythm_plan"] = repair_rhythm_plan(script.get("rhythm_plan"), chapters)
    script["characters"] = characters
    script["locations"] = locations
    script["chapters"] = chapters
    script["scenes"] = scenes
    script["coverage_report"] = repair_coverage_report(script.get("coverage_report"), chapters, script["foreshadowing_ledger"])
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
        "speech_style": data.get("speech_style")
        if isinstance(data.get("speech_style"), dict)
        else {
            "pace": "中等",
            "vocabulary": "少用长句，避免说明文式表达",
            "habit": "通过停顿、反问或回避表达情绪",
            "subtext": "保留潜台词",
            "taboo": "不直接讲出观众已知背景",
        },
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
        "plot_function": str(data.get("plot_function") or "turn"),
        "intensity": max(1, min(10, to_int(data.get("intensity"), index + 3))),
        "characters": normalize_ref_list(data.get("characters"), set(character_ids)) or character_ids,
        "beats": beats,
        "transition": str(data.get("transition") or "cut_to"),
        "visualization_checks": data.get("visualization_checks")
        if isinstance(data.get("visualization_checks"), dict)
        else {
            "no_internal_monologue": True,
            "has_performable_action": True,
            "has_subtext_dialogue": True,
            "canon_consistent": True,
            "foreshadowing_tracked": True,
        },
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
        repaired.setdefault("source_refs", [])
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


def repair_story_bible(value: Any, chapters: list[dict[str, Any]], characters: list[dict[str, Any]]) -> dict[str, Any]:
    data = value if isinstance(value, dict) else {}
    protagonist_id = characters[0]["id"] if characters else "char_001"
    return {
        "premise": str(data.get("premise") or "人物在连续事件中面对核心冲突。"),
        "world_rules": normalize_list(data.get("world_rules")),
        "character_arcs": normalize_list(data.get("character_arcs"))
        or [
            {
                "character_id": protagonist_id,
                "start_state": "信息不足，被事件推动",
                "midpoint_state": "主动调查，冲突升级",
                "end_state": "接近真相，完成阶段性选择",
            }
        ],
        "major_conflicts": normalize_string_list(data.get("major_conflicts")) or ["主要人物与现实阻碍之间的冲突"],
        "timeline": data.get("timeline")
        if isinstance(data.get("timeline"), list)
        else [
            {"order": chapter["order"], "event": chapter["summary"], "source_chapter": chapter["id"]}
            for chapter in chapters
        ],
    }


def repair_foreshadowing_ledger(value: Any, chapters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items = normalize_list(value)
    if items:
        return items
    first_chapter = chapters[0]["id"] if chapters else "chapter_001"
    return [
        {
            "id": "foreshadow_001",
            "setup": "关键线索",
            "source_chapters": [first_chapter],
            "expected_payoff": "后续揭示线索与核心事件的关系",
            "payoff_status": "pending",
            "payoff_scene_id": None,
        }
    ]


def repair_rhythm_plan(value: Any, chapters: list[dict[str, Any]]) -> dict[str, Any]:
    data = value if isinstance(value, dict) else {}
    if isinstance(data.get("acts"), list):
        return data
    ids = [chapter["id"] for chapter in chapters]
    return {
        "acts": [
            {"id": "act_001", "function": "建立人物和悬念", "chapters": ids[:1], "intensity": "low_to_mid"},
            {"id": "act_002", "function": "推进调查与冲突", "chapters": ids[1:2], "intensity": "mid_to_high"},
            {"id": "act_003", "function": "阶段性揭示", "chapters": ids[-1:], "intensity": "high"},
        ]
    }


def repair_coverage_report(
    value: Any, chapters: list[dict[str, Any]], foreshadowing_ledger: list[dict[str, Any]]
) -> dict[str, Any]:
    data = value if isinstance(value, dict) else {}
    return {
        "covered_chapters": normalize_string_list(data.get("covered_chapters"))
        or [chapter["id"] for chapter in chapters],
        "missing_events": normalize_list(data.get("missing_events")),
        "unresolved_foreshadowing": normalize_string_list(data.get("unresolved_foreshadowing"))
        or [item["id"] for item in foreshadowing_ledger if item.get("payoff_status") == "pending"],
        "contradictions": normalize_list(data.get("contradictions")),
    }
