import os
import unittest
from io import BytesIO
from unittest.mock import patch

from novel2script.online_client import LLMConfig, parse_script_json, repair_script
from novel2script.validator import validate_script
from novel2script.server import Novel2ScriptHandler


class OnlineClientTest(unittest.TestCase):
    def test_config_reads_env(self):
        with patch.dict(
            os.environ,
            {
                "LLM_API_KEY": "test-key",
                "LLM_BASE_URL": "https://example.com/v1",
                "LLM_MODEL": "qwen-test",
                "LLM_PROVIDER": "qwen",
            },
        ):
            config = LLMConfig.from_env()

        self.assertEqual(config.api_key, "test-key")
        self.assertEqual(config.base_url, "https://example.com/v1")
        self.assertEqual(config.model, "qwen-test")

    def test_parse_script_json_strips_code_fence(self):
        script = parse_script_json(
            '```json\n{"script":{"schema_version":"1.0","title":"x"}}\n```'
        )

        self.assertEqual(script["schema_version"], "1.0")
        self.assertEqual(script["title"], "x")

    def test_repair_script_normalizes_common_model_drift(self):
        script = {
            "schema_version": "1.0",
            "title": "测试",
            "format": "screenplay",
            "language": "zh-CN",
            "source": {"type": "book", "chapter_count": 3},
            "logline": "测试",
            "synopsis": "测试",
            "characters": [{"id": "char_001", "name": "林舟"}],
            "locations": [{"id": "loc_001", "name": "旧书店"}],
            "chapters": [
                {"id": "chapter_001", "title": "一", "order": "1", "summary": "一"},
                {"id": "chapter_002", "title": "二", "order": "2", "summary": "二"},
                {"id": "chapter_003", "title": "三", "order": "3", "summary": "三"},
            ],
            "scenes": [
                {
                    "id": "scn_001",
                    "order": "1",
                    "beats": [
                        {"type": "action", "content": "林舟走进旧书店。"},
                        {"type": "dialogue", "dialogue_text": "有人来过吗？"},
                    ],
                }
            ],
            "notes": [],
        }

        repaired = repair_script(script, "第一章\n一\n\n第二章\n二\n\n第三章\n三", "测试", "screenplay")

        self.assertEqual(validate_script(repaired), [])
        self.assertEqual(repaired["source"]["type"], "novel")
        self.assertEqual(repaired["scenes"][0]["id"], "scene_001")
        self.assertEqual(repaired["scenes"][0]["beats"][0]["text"], "林舟走进旧书店。")


class FakeRequestHandler(Novel2ScriptHandler):
    def __init__(self) -> None:
        self.headers = {"Content-Length": "2"}
        self.rfile = BytesIO(b"{}")
        self.wfile = BytesIO()


class ServerHandlerTest(unittest.TestCase):
    def test_resolve_index(self):
        handler = FakeRequestHandler()
        handler.path = "/"

        path = handler.resolve_static_path()

        self.assertIsNotNone(path)
        self.assertEqual(path.name, "index.html")

    def test_resolve_unknown_path(self):
        handler = FakeRequestHandler()
        handler.path = "/missing-file"

        self.assertIsNone(handler.resolve_static_path())


if __name__ == "__main__":
    unittest.main()
