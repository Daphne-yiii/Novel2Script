from __future__ import annotations

from typing import Any


def dump_yaml(data: dict[str, Any]) -> str:
    return _dump_value(data, 0).rstrip() + "\n"


def _dump_value(value: Any, indent: int) -> str:
    if isinstance(value, dict):
        return _dump_dict(value, indent)
    if isinstance(value, list):
        return _dump_list(value, indent)
    return " " * indent + _format_scalar(value) + "\n"


def _dump_dict(data: dict[str, Any], indent: int) -> str:
    lines: list[str] = []
    prefix = " " * indent
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{prefix}{key}:")
            lines.append(_dump_dict(value, indent + 2).rstrip())
        elif isinstance(value, list):
            if value:
                lines.append(f"{prefix}{key}:")
                lines.append(_dump_list(value, indent + 2).rstrip())
            else:
                lines.append(f"{prefix}{key}: []")
        else:
            lines.append(f"{prefix}{key}: {_format_scalar(value)}")
    return "\n".join(lines) + "\n"


def _dump_list(items: list[Any], indent: int) -> str:
    lines: list[str] = []
    prefix = " " * indent
    for item in items:
        if isinstance(item, dict):
            lines.append(f"{prefix}- {first_dict_key_line(item)}")
            remaining = dict(list(item.items())[1:])
            if remaining:
                lines.append(_dump_dict(remaining, indent + 2).rstrip())
        elif isinstance(item, list):
            lines.append(f"{prefix}-")
            lines.append(_dump_list(item, indent + 2).rstrip())
        else:
            lines.append(f"{prefix}- {_format_scalar(item)}")
    return "\n".join(lines) + "\n"


def first_dict_key_line(item: dict[str, Any]) -> str:
    if not item:
        return "{}"

    key, value = next(iter(item.items()))
    if isinstance(value, dict):
        nested = _dump_dict(value, 4).rstrip()
        return f"{key}:\n{nested}"
    if isinstance(value, list):
        if not value:
            return f"{key}: []"
        nested = _dump_list(value, 4).rstrip()
        return f"{key}:\n{nested}"
    return f"{key}: {_format_scalar(value)}"


def _format_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value)
    escaped = (
        text.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\t", "\\t")
    )
    return f'"{escaped}"'
