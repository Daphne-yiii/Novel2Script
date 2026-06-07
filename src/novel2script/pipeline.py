from __future__ import annotations

from typing import Any

from .adaptation_planner import AdaptationPlanner
from .chapter_segmenter import ChapterSegmenter
from .composer import YAMLComposer
from .errors import PipelineError
from .input_parser import InputParser
from .quality_rewriter import SceneQualityRewriter
from .scene_writer import SceneWriter
from .story_analyzer import StoryAnalyzer
from .validator import validate_script


class Novel2ScriptPipeline:
    """Local Agent Pipeline for converting novel text into screenplay YAML data."""

    def __init__(self, format: str = "screenplay") -> None:
        self.format = format
        self.input_parser = InputParser()
        self.chapter_segmenter = ChapterSegmenter()
        self.story_analyzer = StoryAnalyzer()
        self.adaptation_planner = AdaptationPlanner()
        self.scene_writer = SceneWriter()
        self.scene_quality_rewriter = SceneQualityRewriter()
        self.yaml_composer = YAMLComposer()

    def run(self, text: str, title: str | None = None) -> dict[str, Any]:
        cleaned_text = self.input_parser.parse(text)
        chapters = self.chapter_segmenter.segment(cleaned_text)
        if len(chapters) < 3:
            raise PipelineError("输入章节少于 3 个，无法生成剧本。")

        analysis = self.story_analyzer.analyze(cleaned_text, chapters)
        plan = self.adaptation_planner.plan(chapters, analysis)
        scenes = self.scene_writer.write(chapters, analysis, plan)
        chapters_by_id = {chapter.id: chapter for chapter in chapters}
        scenes = self.scene_quality_rewriter.rewrite(scenes, chapters_by_id)
        script = self.yaml_composer.compose(
            chapters,
            analysis,
            scenes,
            title=title,
            script_format=self.format,
        )

        errors = validate_script(script)
        if errors:
            raise PipelineError("YAML Schema 校验失败：" + "；".join(errors))
        return script
