#!/usr/bin/env python3
"""Render `codex exec --json` output into a readable terminal stream."""

from __future__ import annotations

import json
import re
import sys
from typing import Iterable

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

USE_COLOR = sys.stdout.isatty()
RESET = "\033[0m" if USE_COLOR else ""
DIM = "\033[2m" if USE_COLOR else ""
BOLD = "\033[1m" if USE_COLOR else ""
RED = "\033[31m" if USE_COLOR else ""
CYAN = "\033[36m" if USE_COLOR else ""


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


def emit_prefixed(lines: Iterable[str], prefix: str = "  ") -> None:
    for line in lines:
        emit(f"{prefix}{line}")


def emit_block(lines: Iterable[str]) -> None:
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
    lines = [line.rstrip() for line in stripped.splitlines() if line.strip()]
    if not lines:
        return

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


def render_event(event: dict) -> None:
    event_type = event.get("type")
    item = event.get("item") or {}
    item_type = item.get("type")

    if event_type == "item.completed" and item_type == "agent_message":
        text = item.get("text", "").strip()
        if text:
            render_agent_message(clean_text(text))
        return

    if event_type == "item.started" and item_type == "todo_list":
        lines = [section("Plan")]
        for todo in item.get("items", []):
            marker = "x" if todo.get("completed") else " "
            lines.append(f"  [{marker}] {todo.get('text', '')}")
        emit_block(lines)
        return

    if item_type == "command_execution":
        command = compact(item.get("command", ""))
        if event_type == "item.started":
            emit(f"[run] {command}")
            return

        if event_type == "item.completed":
            exit_code = item.get("exit_code")
            status = item.get("status")
            if status == "completed" and exit_code == 0:
                emit(style_ok(f"[ok]  {command}"))
                return

            lines = [
                style_fail("!!! FAILURE !!!"),
                style_fail(f"[fail] {command} (exit {exit_code})"),
            ]
            output = item.get("aggregated_output", "")
            excerpt = important_lines(output)
            if excerpt:
                lines.extend(f"  {line}" for line in excerpt)
            emit_block(lines)
            return

    if event_type == "item.completed" and item_type == "file_change":
        changes = item.get("changes", [])
        paths = [change.get("path", "") for change in changes if change.get("path")]
        if paths:
            emit_block([section("Changed files"), *(f"  {path}" for path in paths)])
        return

    if event_type == "error":
        message = event.get("message") or event.get("error") or "Unknown error"
        emit_block([style_fail("!!! ERROR !!!"), style_fail(f"[error] {clean_text(message)}")])


def main() -> int:
    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue

        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            emit(strip_ansi(line))
            continue

        render_event(event)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
