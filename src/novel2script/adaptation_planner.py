from __future__ import annotations

from .models import AdaptationPlan, Chapter, Location, ScenePlan, StoryAnalysis
from .text_utils import infer_interior_exterior, infer_time_of_day


class AdaptationPlanner:
    """Plan how source chapters become screenplay scenes."""

    def plan(self, chapters: list[Chapter], analysis: StoryAnalysis) -> AdaptationPlan:
        scenes = [
            ScenePlan(
                id=f"scene_{index:03d}",
                order=index,
                source_chapters=[chapter.id],
                location_id=choose_location_for_chapter(chapter.text, analysis.locations).id,
                time_of_day=infer_time_of_day(chapter.text),
                interior_exterior=infer_interior_exterior(chapter.text),
                purpose=infer_scene_purpose(index, len(chapters)),
                plot_function=infer_plot_function(index, len(chapters), chapter.text),
                intensity=infer_intensity(index, len(chapters), chapter.text),
                character_ids=[character.id for character in analysis.characters[:3]],
                rewrite_strategy=infer_rewrite_strategy(chapter.text),
            )
            for index, chapter in enumerate(chapters, start=1)
        ]
        return AdaptationPlan(scenes=scenes)


def choose_location_for_chapter(text: str, locations: list[Location]) -> Location:
    for location in locations:
        if location.name in text:
            return location
    return locations[0]


def infer_scene_purpose(order: int, total: int) -> str:
    if order == 1:
        return "建立故事开端，交代人物处境与核心悬念。"
    if order == total:
        return "推动阶段性揭示，为后续冲突或结局留下明确方向。"
    return "推进调查与人物关系，制造新的冲突或转折。"


def infer_plot_function(order: int, total: int, text: str) -> str:
    if order == 1:
        return "setup"
    if order == total:
        return "payoff"
    if any(keyword in text for keyword in ["发现", "终于", "真相", "名字"]):
        return "reveal"
    return "turn"


def infer_intensity(order: int, total: int, text: str) -> int:
    base = 3 + min(4, order)
    if order == total:
        base = 8
    if any(keyword in text for keyword in ["冲突", "怒", "死", "血", "真相", "旧案"]):
        base += 1
    return max(1, min(10, base))


def infer_rewrite_strategy(text: str) -> list[str]:
    strategy = ["保留章节主事件", "转写为可拍摄动作"]
    if any(keyword in text for keyword in ["想起", "心里", "觉得", "意识到"]):
        strategy.append("将心理描写转为动作、表情或停顿")
    if "“" in text and "”" in text:
        strategy.append("保留并口语化关键对白")
    if len(text) > 220:
        strategy.append("压缩背景说明，必要时转为旁白")
    return strategy
