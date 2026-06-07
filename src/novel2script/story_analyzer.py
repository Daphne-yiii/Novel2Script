from __future__ import annotations

import re

from .models import Chapter, Character, Location, StoryAnalysis


class StoryAnalyzer:
    """Extract story entities and global understanding from chapters."""

    def analyze(self, cleaned_text: str, chapters: list[Chapter]) -> StoryAnalysis:
        characters = extract_characters(cleaned_text)
        locations = extract_locations(cleaned_text)
        timeline = [chapter.summary for chapter in chapters]
        major_events = [chapter.summary for chapter in chapters if chapter.summary]
        tone = infer_tone(cleaned_text)
        conflicts = infer_conflicts(cleaned_text, characters)
        story_bible = build_story_bible(chapters, characters, conflicts)
        foreshadowing_ledger = build_foreshadowing_ledger(cleaned_text, chapters)
        canon_facts = build_canon_facts(cleaned_text, characters, chapters)
        rhythm_plan = build_rhythm_plan(chapters)
        coverage_report = build_initial_coverage_report(chapters, foreshadowing_ledger)
        return StoryAnalysis(
            characters=characters,
            locations=locations,
            timeline=timeline,
            major_events=major_events,
            tone=tone,
            conflicts=conflicts,
            story_bible=story_bible,
            foreshadowing_ledger=foreshadowing_ledger,
            canon_facts=canon_facts,
            rhythm_plan=rhythm_plan,
            coverage_report=coverage_report,
        )


def extract_characters(text: str) -> list[Character]:
    candidates: dict[str, int] = {}
    patterns = [
        r"(?:^|[。！？!?，,\n])\s*([\u4e00-\u9fa5]{2,6})(?:低声|轻声|沉声)?(?:说|问|喊|叫|回答|道)",
        r"“[^”]{1,80}”\s*([\u4e00-\u9fa5]{2,6})(?:低声|轻声|沉声)?(?:说|问|喊|叫|回答|道)",
        r"(?:^|[。！？!?，,\n])\s*([\u4e00-\u9fa5]{2,4})(?:走进|推开|看着|望向|站在|坐在|回到|停住)",
    ]
    stopwords = {
        "他们",
        "她们",
        "我们",
        "你们",
        "有人",
        "孩子",
        "声音",
        "雨水",
        "时候",
        "这里",
        "那里",
        "窗外",
        "街道",
        "房间",
        "书店",
    }
    for pattern in patterns:
        for name in re.findall(pattern, text):
            normalized = normalize_character_name(name)
            if normalized and normalized not in stopwords:
                candidates[normalized] = candidates.get(normalized, 0) + 1

    ranked = sorted(candidates.items(), key=lambda item: (-item[1], item[0]))[:8]
    if not ranked:
        ranked = [("unknown", 1)]

    characters: list[Character] = []
    for index, (name, _) in enumerate(ranked, start=1):
        role = "protagonist" if index == 1 else "supporting"
        display_name = "未知人物" if name == "unknown" else name
        characters.append(
            Character(
                id=f"char_{index:03d}",
                name=display_name,
                role=role,
                description=f"{display_name}，由小说文本自动识别或补全的人物。",
                traits=infer_traits(text, display_name),
                speech_style=infer_speech_style(text, display_name, role),
            )
        )
    return characters


def normalize_character_name(name: str) -> str:
    name = name.strip()
    name = re.sub(r"(低声|轻声|沉声|忽然|终于)$", "", name)
    name = re.sub(r"^(那个|这个|一名|一个)", "", name)
    invalid_fragments = [
        "知道",
        "像是",
        "早就",
        "街",
        "窗",
        "雨",
        "信",
        "房",
        "门",
        "医院",
        "柜台",
        "外",
    ]
    if len(name) < 2 or any(fragment in name for fragment in invalid_fragments):
        return ""
    if name.endswith(("的", "了", "着", "过", "没有", "不是")):
        return ""
    return name


def infer_traits(text: str, name: str) -> list[str]:
    window_pattern = re.compile(rf".{{0,20}}{re.escape(name)}.{{0,30}}")
    windows = " ".join(window_pattern.findall(text))
    traits: list[str] = []
    trait_keywords = [
        ("沉默", "克制"),
        ("犹豫", "谨慎"),
        ("追问", "执着"),
        ("冷笑", "冷静"),
        ("害怕", "敏感"),
        ("怒", "冲动"),
    ]
    for keyword, trait in trait_keywords:
        if keyword in windows and trait not in traits:
            traits.append(trait)
    return traits or ["待细化"]


def infer_speech_style(text: str, name: str, role: str) -> dict[str, str]:
    pace = "慢" if any(keyword in text for keyword in ["沉默", "低声", "停住", "没有回答"]) else "中等"
    if role == "protagonist":
        habit = "常用反问和停顿，不直接表达真实情绪"
        subtext = "用克制语气掩盖怀疑、愤怒或恐惧"
    else:
        habit = "根据场景压力调整表达，避免长篇解释"
        subtext = "通过回避和试探传递隐藏信息"
    return {
        "pace": pace,
        "vocabulary": "少用长句，避免说明文式表达",
        "habit": habit,
        "subtext": subtext,
        "taboo": "不主动说出观众已经知道的背景信息",
    }


def extract_locations(text: str) -> list[Location]:
    keywords = [
        "书店",
        "房间",
        "街道",
        "巷子",
        "办公室",
        "学校",
        "医院",
        "车站",
        "屋里",
        "门口",
        "客厅",
        "厨房",
    ]
    found: list[str] = []
    for keyword in keywords:
        if keyword in text and keyword not in found:
            found.append(keyword)

    if not found:
        found = ["主要场景"]

    return [
        Location(
            id=f"loc_{index:03d}",
            name=name,
            description=f"{name}，由小说文本自动识别或补全的场景空间。",
        )
        for index, name in enumerate(found[:8], start=1)
    ]


def infer_tone(text: str) -> str:
    if any(keyword in text for keyword in ["雨", "信", "失踪", "旧案", "秘密", "沉默"]):
        return "悬疑克制"
    if any(keyword in text for keyword in ["笑", "阳光", "热闹", "欢呼"]):
        return "明亮轻快"
    return "写实叙事"


def infer_conflicts(text: str, characters: list[Character]) -> list[str]:
    conflicts: list[str] = []
    if any(keyword in text for keyword in ["信", "秘密", "真相", "旧案"]):
        conflicts.append("人物追寻真相与未知阻力之间的冲突。")
    if any(keyword in text for keyword in ["沉默", "没有回答", "犹豫"]):
        conflicts.append("人物之间因隐瞒和试探产生的关系冲突。")
    if not conflicts:
        protagonist = characters[0].name if characters else "主角"
        conflicts.append(f"{protagonist}的目标与现实阻碍之间的冲突。")
    return conflicts


def build_story_bible(
    chapters: list[Chapter], characters: list[Character], conflicts: list[str]
) -> dict:
    protagonist = characters[0] if characters else None
    return {
        "premise": conflicts[0] if conflicts else "人物在连续事件中面对现实阻碍。",
        "world_rules": infer_world_rules(chapters),
        "character_arcs": [
            {
                "character_id": protagonist.id,
                "start_state": "被事件推入悬念，信息不足",
                "midpoint_state": "开始主动调查并承受关系压力",
                "end_state": "接近真相，完成阶段性选择",
            }
        ]
        if protagonist
        else [],
        "major_conflicts": conflicts,
        "timeline": [
            {
                "order": chapter.order,
                "event": chapter.summary,
                "source_chapter": chapter.id,
            }
            for chapter in chapters
        ],
    }


def infer_world_rules(chapters: list[Chapter]) -> list[dict]:
    rules: list[dict] = []
    for chapter in chapters:
        if any(keyword in chapter.text for keyword in ["不会武功", "从未学过武", "没有学过武"]):
            rules.append(
                {
                    "id": f"rule_{len(rules) + 1:03d}",
                    "text": "主角当前阶段不会武功",
                    "source_chapters": [chapter.id],
                }
            )
    return rules


def build_foreshadowing_ledger(text: str, chapters: list[Chapter]) -> list[dict]:
    clue_keywords = ["信", "印章", "照片", "钥匙", "旧案", "名字", "日期", "录音"]
    ledger: list[dict] = []
    for chapter in chapters:
        for keyword in clue_keywords:
            if keyword in chapter.text and not any(item["setup"] == keyword for item in ledger):
                ledger.append(
                    {
                        "id": f"foreshadow_{len(ledger) + 1:03d}",
                        "setup": keyword,
                        "source_chapters": [chapter.id],
                        "expected_payoff": f"后续揭示“{keyword}”与核心事件的关系",
                        "payoff_status": "pending",
                        "payoff_scene_id": None,
                    }
                )
    return ledger[:8]


def build_canon_facts(
    text: str, characters: list[Character], chapters: list[Chapter]
) -> list[dict]:
    facts: list[dict] = []
    protagonist = characters[0].name if characters else "主角"
    if any(keyword in text for keyword in ["不会武功", "从未学过武", "没有学过武"]):
        facts.append(
            {
                "id": "fact_001",
                "subject": protagonist,
                "predicate": "不会",
                "object": "武功",
                "valid_from": chapters[0].id,
                "valid_until": chapters[-1].id,
                "source_text": "文本显示人物当前阶段没有武力能力。",
            }
        )
    return facts


def build_rhythm_plan(chapters: list[Chapter]) -> dict:
    first = chapters[0].id
    middle = chapters[len(chapters) // 2].id
    last = chapters[-1].id
    return {
        "acts": [
            {
                "id": "act_001",
                "function": "建立世界、人物和核心悬念",
                "chapters": [first],
                "intensity": "low_to_mid",
            },
            {
                "id": "act_002",
                "function": "调查推进，冲突升级",
                "chapters": [middle],
                "intensity": "mid_to_high",
            },
            {
                "id": "act_003",
                "function": "阶段性揭示与情感转折",
                "chapters": [last],
                "intensity": "high",
            },
        ]
    }


def build_initial_coverage_report(
    chapters: list[Chapter], foreshadowing_ledger: list[dict]
) -> dict:
    return {
        "covered_chapters": [chapter.id for chapter in chapters],
        "missing_events": [],
        "unresolved_foreshadowing": [
            item["id"] for item in foreshadowing_ledger if item.get("payoff_status") == "pending"
        ],
        "contradictions": [],
    }
