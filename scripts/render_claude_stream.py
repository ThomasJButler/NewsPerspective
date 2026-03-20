#!/usr/bin/env python3
"""Render Claude Code stream-json output into a readable terminal stream."""

from __future__ import annotations

import json
import re
import sys
from typing import Any

ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")
IMPORTANT_OUTPUT_PATTERNS = (
    "error",
    "failed",
    "fatal",
    "panic",
    "exception",
    "traceback",
    "caused by",
    "operation not permitted",
)
EDIT_TOOL_NAMES = {"Edit", "MultiEdit", "Write", "NotebookEdit"}

USE_COLOR = sys.stdout.isatty()
RESET = "\033[0m" if USE_COLOR else ""
DIM = "\033[2m" if USE_COLOR else ""
BOLD = "\033[1m" if USE_COLOR else ""
RED = "\033[31m" if USE_COLOR else ""
CYAN = "\033[36m" if USE_COLOR else ""

pending_tools: dict[str, str] = {}
seen_changed_files: set[str] = set()


def strip_ansi(text: str) -> str:
    return ANSI_ESCAPE_RE.sub("", text)


def clean_text(text: str) -> str:
    return CONTROL_CHARS_RE.sub("", strip_ansi(text))


def compact(text: str, limit: int = 160) -> str:
    single_line = " ".join(clean_text(text).split())
    if len(single_line) <= limit:
        return single_line
    return f"{single_line[: limit - 3]}..."


def important_lines(text: str) -> list[str]:
    cleaned = [clean_text(line).rstrip() for line in text.splitlines()]
    non_empty = [line for line in cleaned if line.strip()]
    matches: list[str] = []

    for line in non_empty:
        lowered = line.lower()
        if any(pattern in lowered for pattern in IMPORTANT_OUTPUT_PATTERNS):
            if line not in matches:
                matches.append(line)

    if matches:
        return matches[:12]

    return non_empty[-12:]


def emit(text: str = "") -> None:
    print(text, flush=True)


def emit_block(lines: list[str]) -> None:
    for line in lines:
        emit(line)
    emit()


def quoted(text: str) -> str:
    normalized = " ".join(text.split())
    escaped = normalized.replace('"', "'")
    return f'"{escaped}"'


def section(title: str) -> str:
    return f"{BOLD}{CYAN}=== {title} ==={RESET}"


def style_ok(text: str) -> str:
    return f"{DIM}{text}{RESET}" if USE_COLOR else text


def style_fail(text: str) -> str:
    return f"{BOLD}{RED}{text}{RESET}" if USE_COLOR else text


def render_labeled_block(title: str, body_lines: list[str]) -> None:
    emit_block([section(title), *body_lines])


def render_agent_message(text: str) -> None:
    stripped = text.strip()
    if not stripped:
        return

    lines = [line.rstrip() for line in stripped.splitlines() if line.strip()]
    heading = lines[0].rstrip(":").lower()

    if heading == "simple":
        render_labeled_block("Simple", [f"  {line}" for line in lines[1:]])
        return

    if heading == "insight":
        render_labeled_block("Insight", [f"  {line}" for line in lines[1:]])
        return

    if heading == "checkpoint":
        render_labeled_block("Checkpoint", [f"  {line}" for line in lines[1:]])
        return

    if heading == "summary":
        render_labeled_block("Summary", [f"  {line}" for line in lines[1:]])
        return

    emit_block([quoted(stripped)])


def extract_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text = item.get("text")
                if isinstance(text, str) and text.strip():
                    parts.append(text)
            elif isinstance(item, str) and item.strip():
                parts.append(item)
        return "\n".join(parts)
    return ""


def command_from_tool_input(name: str, tool_input: Any) -> str:
    if not isinstance(tool_input, dict):
        return name

    for key in ("command", "cmd", "prompt", "description", "pattern", "query"):
        value = tool_input.get(key)
        if isinstance(value, str) and value.strip():
            return value

    if name in EDIT_TOOL_NAMES:
        file_path = tool_input.get("file_path")
        if isinstance(file_path, str) and file_path.strip():
            return f"{name} {file_path}"

    return name


def maybe_emit_changed_file(tool_input: Any) -> None:
    if not isinstance(tool_input, dict):
        return

    file_path = tool_input.get("file_path")
    if not isinstance(file_path, str) or not file_path.strip():
        return

    if file_path in seen_changed_files:
        return

    seen_changed_files.add(file_path)
    emit_block([section("Changed files"), f"  {file_path}"])


def maybe_render_todo_write(tool_input: Any) -> bool:
    if not isinstance(tool_input, dict):
        return False

    todos = tool_input.get("todos")
    if not isinstance(todos, list):
        return False

    lines = [section("Plan")]
    for todo in todos:
        if not isinstance(todo, dict):
            continue
        status = todo.get("status")
        marker = "x" if status == "completed" else " "
        content = todo.get("content") or todo.get("text") or ""
        lines.append(f"  [{marker}] {content}")
    emit_block(lines)
    return True


def render_tool_use(block: dict[str, Any]) -> None:
    tool_name = str(block.get("name", "")).strip()
    tool_input = block.get("input")
    tool_id = str(block.get("id", "")).strip()

    if tool_name == "TodoWrite" and maybe_render_todo_write(tool_input):
        if tool_id:
            pending_tools[tool_id] = "TodoWrite"
        return

    if tool_name in EDIT_TOOL_NAMES:
        maybe_emit_changed_file(tool_input)

    label = compact(command_from_tool_input(tool_name or "tool", tool_input))
    emit(f"[run] {label}")
    if tool_id:
        pending_tools[tool_id] = label


def render_tool_result(block: dict[str, Any]) -> None:
    tool_id = str(block.get("tool_use_id", "")).strip()
    label = pending_tools.pop(tool_id, "tool result")
    is_error = bool(block.get("is_error"))
    output = extract_text(block.get("content", ""))

    if is_error:
        lines = [
            style_fail("!!! FAILURE !!!"),
            style_fail(f"[fail] {label}"),
        ]
        excerpt = important_lines(output)
        if excerpt:
            lines.extend(f"  {line}" for line in excerpt)
        emit_block(lines)
        return

    emit(style_ok(f"[ok]  {label}"))


def render_message(message: dict[str, Any]) -> None:
    content = message.get("content")
    if not isinstance(content, list):
        return

    for block in content:
        if not isinstance(block, dict):
            continue

        block_type = block.get("type")
        if block_type == "text":
            text = block.get("text")
            if isinstance(text, str) and text.strip():
                render_agent_message(clean_text(text))
        elif block_type == "tool_use":
            render_tool_use(block)
        elif block_type == "tool_result":
            render_tool_result(block)


def render_result(event: dict[str, Any]) -> None:
    if event.get("subtype") == "success":
        return

    result_text = event.get("result")
    if isinstance(result_text, str) and result_text.strip():
        lines = [
            style_fail("!!! FAILURE !!!"),
            style_fail("[fail] Claude Code run ended with an error"),
        ]
        lines.extend(f"  {line}" for line in important_lines(result_text))
        emit_block(lines)


def render_event(event: dict[str, Any]) -> None:
    event_type = event.get("type")

    message = event.get("message")
    if isinstance(message, dict):
        render_message(message)
        return

    if event_type == "result":
        render_result(event)
        return

    if event_type == "assistant":
        render_message(event)
        return

    if event_type == "user":
        render_message(event)
        return

    if event_type == "error":
        message_text = event.get("message") or event.get("error") or "Unknown error"
        emit_block([style_fail("!!! ERROR !!!"), style_fail(f"[error] {clean_text(str(message_text))}")])


def main() -> int:
    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue

        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            emit(clean_text(line))
            continue

        if isinstance(event, dict):
            render_event(event)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
