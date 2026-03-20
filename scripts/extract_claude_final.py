#!/usr/bin/env python3
"""Extract the final assistant response from a Claude Code stream-json log."""

from __future__ import annotations

import json
import sys
from typing import Any


def text_from_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text = item.get("text")
                if isinstance(text, str) and text.strip():
                    parts.append(text)
        return "\n".join(parts)
    return ""


def main() -> int:
    final_result = ""
    last_assistant_text = ""

    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue

        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        event_type = event.get("type")
        if event_type == "result":
            result = event.get("result")
            if isinstance(result, str) and result.strip():
                final_result = result

        message = event.get("message")
        if (
            isinstance(message, dict)
            and message.get("role") == "assistant"
            and isinstance(message.get("content"), list)
        ):
            text = text_from_content(message["content"]).strip()
            if text:
                last_assistant_text = text

    output = (final_result or last_assistant_text).strip()
    if output:
        sys.stdout.write(output)
        if not output.endswith("\n"):
            sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
