from __future__ import annotations

import argparse
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from .errors import PipelineError
from .online_client import generate_script_with_llm
from .pipeline import Novel2ScriptPipeline
from .yaml_writer import dump_yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Novel2ScriptHandler(BaseHTTPRequestHandler):
    server_version = "Novel2Script/0.1"

    def do_GET(self) -> None:
        if self.path.split("?", 1)[0] == "/api/convert":
            self.send_json(
                {
                    "ok": True,
                    "endpoint": "/api/convert",
                    "method": "POST",
                    "message": "请使用 POST 请求提交 title、format、source 和 mode。",
                }
            )
            return
        if self.path.split("?", 1)[0] == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return

        path = self.resolve_static_path()
        if path is None:
            self.send_error(404)
            return
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        if self.path != "/api/convert":
            self.send_json({"ok": False, "error": "unknown endpoint"}, status=404)
            return

        try:
            payload = self.read_json()
            source = str(payload.get("source", ""))
            title = str(payload.get("title", ""))
            script_format = str(payload.get("format", "screenplay"))
            mode = str(payload.get("mode", "online"))

            if mode == "offline":
                script = Novel2ScriptPipeline(format=script_format).run(source, title=title or None)
            else:
                script = generate_script_with_llm(source, title=title, script_format=script_format)
            yaml_text = dump_yaml({"script": script})
            self.send_json({"ok": True, "yaml": yaml_text, "script": script})
        except PipelineError as exc:
            print(f"/api/convert error: {exc}")
            self.send_json({"ok": False, "error": str(exc)}, status=400)
        except Exception as exc:  # noqa: BLE001 - keep browser-facing errors friendly.
            print(f"/api/convert unexpected error: {exc}")
            self.send_json({"ok": False, "error": f"哎呀，出错了，请重启试试吧~ {exc}"}, status=500)

    def resolve_static_path(self) -> Path | None:
        raw_path = self.path.split("?", 1)[0]
        if raw_path == "/":
            raw_path = "/index.html"
        relative = unquote(raw_path).lstrip("/")
        candidate = (PROJECT_ROOT / relative).resolve()
        if PROJECT_ROOT not in candidate.parents and candidate != PROJECT_ROOT:
            return None
        if not candidate.exists() or not candidate.is_file():
            return None
        return candidate

    def read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length).decode("utf-8")
        data = json.loads(body or "{}")
        if not isinstance(data, dict):
            raise PipelineError("请求体必须是 JSON 对象。")
        return data

    def send_json(self, payload: dict[str, Any], status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        print(f"{self.address_string()} - {format % args}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Novel2Script web server.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8000, type=int)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    server = ThreadingHTTPServer((args.host, args.port), Novel2ScriptHandler)
    url = f"http://{args.host}:{args.port}"
    print(f"Novel2Script server running at {url}")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
