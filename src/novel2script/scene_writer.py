from __future__ import annotations
from typing import Any
from .models import AdaptationPlan, Chapter, Character, ScenePlan, StoryAnalysis

class SceneWriter:
    """Generate professional screenplay scenes using director-level instructions."""

    def write(
        self,
        chapters: list[Chapter],
        analysis: StoryAnalysis,
        plan: AdaptationPlan,
    ) -> list[dict[str, Any]]:
        chapters_by_id = {chapter.id: chapter for chapter in chapters}
        scenes: list[dict[str, Any]] = []
        
        
        char_map = {c.id: c for c in analysis.characters}
        
        for scene_plan in plan.scenes:
            chapter = chapters_by_id[scene_plan.source_chapters[0]]
            
            scenes.append(write_scene(scene_plan, chapter, char_map))
        return scenes

def write_scene(
    scene_plan: ScenePlan,
    chapter: Chapter,
    char_map: dict[str, Character],
) -> dict[str, Any]:
    

    char_context = "\n".join([
        f"- {c.name}: {c.visual_anchor}, 说话风格: {c.speech_style}" 
        for c in char_map.values()
    ])
    
  
    beats = [
        {
            "type": "action",
            "text": (
                f"【导演指令：{scene_plan.visual_narrative_plan}】\n"
                f"画面呈现：{chapter.summary}。注意使用以下视觉锚点：{char_context}"
            ),
        },
        {
            "type": "action",
            "text": f"【潜台词博弈：{scene_plan.subtext_conflict}】——在此场景中，人物对话需体现掩饰或试探，禁止直白交流。"
        }
    ]

    
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
        "plot_function": scene_plan.plot_function,
        "intensity": scene_plan.intensity,
        "characters": scene_plan.character_ids,
        "beats": beats,
        "transition": "cut_to",
       
        "metadata": {
            "subtext": scene_plan.subtext_conflict,
            "visual_plan": scene_plan.visual_narrative_plan
        }
    }
