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
        return StoryAnalysis(
            characters=characters,
            locations=locations,
            timeline=timeline,
            major_events=major_events,
            tone=tone,
            conflicts=conflicts,
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
