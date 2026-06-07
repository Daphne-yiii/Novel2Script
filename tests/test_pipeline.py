import unittest

from novel2script.pipeline import Novel2ScriptPipeline, PipelineError
from novel2script.validator import validate_script
from novel2script.yaml_writer import dump_yaml


SAMPLE = """
第一章 雨夜
林舟推开旧书店的门，雨水从伞尖落下。
“有人来过吗？”林舟问。
老人把一封信推到柜台边。

第二章 追问
林舟回到房间，反复看那封没有署名的信。
“这不是巧合。”林舟低声说。
窗外的街道被雨水照得发白。

第三章 旧案
清晨，林舟来到医院门口，终于看见信中提到的名字。
“你终于来了。”女人说。
林舟停住脚步，旧案的轮廓浮出水面。
"""


class PipelineTest(unittest.TestCase):
    def test_pipeline_generates_valid_script(self):
        script = Novel2ScriptPipeline().run(SAMPLE, title="雨夜来信")

        self.assertEqual(script["title"], "雨夜来信")
        self.assertEqual(script["source"]["chapter_count"], 3)
        self.assertEqual(len(script["chapters"]), 3)
        self.assertEqual(len(script["scenes"]), 3)
        self.assertEqual(script["scenes"][0]["source_chapters"], ["chapter_001"])
        self.assertIn("location_id", script["scenes"][0]["heading"])
        self.assertIn("story_bible", script)
        self.assertIn("foreshadowing_ledger", script)
        self.assertIn("canon_facts", script)
        self.assertIn("rhythm_plan", script)
        self.assertIn("coverage_report", script)
        self.assertIn("visualization_checks", script["scenes"][0])
        self.assertIn("source_refs", script["scenes"][0]["beats"][0])
        self.assertEqual(validate_script(script), [])

    def test_yaml_writer_outputs_script_root(self):
        script = Novel2ScriptPipeline().run(SAMPLE)
        yaml_text = dump_yaml({"script": script})

        self.assertTrue(yaml_text.startswith("script:\n"))
        self.assertIn('schema_version: "1.0"', yaml_text)
        self.assertIn("scenes:", yaml_text)

    def test_rejects_too_few_chapters(self):
        with self.assertRaisesRegex(PipelineError, "输入章节少于 3 个"):
            Novel2ScriptPipeline().run("第一章\n只有一个章节。")


if __name__ == "__main__":
    unittest.main()
