from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .pipeline import Novel2ScriptPipeline, PipelineError
from .yaml_writer import dump_yaml


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="novel2script",
        description="Convert a Chinese novel text into structured screenplay YAML.",
    )
    parser.add_argument("input", help="Path to the source novel text file.")
    parser.add_argument(
        "-o",
        "--output",
        help="Path to write the generated YAML. Defaults to stdout.",
    )
    parser.add_argument(
        "--title",
        help="Override the generated screenplay title.",
    )
    parser.add_argument(
        "--format",
        default="screenplay",
        choices=["screenplay", "web_series", "stage_play", "audio_drama"],
        help="Target script format.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"error: input file not found: {input_path}", file=sys.stderr)
        return 2

    try:
        text = input_path.read_text(encoding="utf-8")
        pipeline = Novel2ScriptPipeline(format=args.format)
        script = pipeline.run(text, title=args.title)
        yaml_text = dump_yaml({"script": script})
    except UnicodeDecodeError:
        print("error: input file must be UTF-8 encoded.", file=sys.stderr)
        return 2
    except PipelineError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.output:
        Path(args.output).write_text(yaml_text, encoding="utf-8")
    else:
        print(yaml_text, end="")

    return 0
