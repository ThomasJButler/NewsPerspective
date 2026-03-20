#!/usr/bin/env python3
"""Interactive coach dashboard for Ralph loop JSONL streams.

Provides Docker/npm-style terminal output with spinners, phase banners,
checkmarks, labelled blocks, and a summary box.

Usage:
    python3 render_coach_dashboard.py <jsonl_path>
    python3 render_coach_dashboard.py .claude-run/build-20260319-143512.jsonl
"""

from __future__ import annotations

import json
import os
import re
import shutil
import signal
import sys
import time
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SPINNER_FRAMES = "\u280b\u2819\u2839\u2838\u283c\u2834\u2826\u2827\u2807\u280f"
POLL_INTERVAL = 0.1  # 100ms — smooth 10fps spinner

ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b-\x1f\x7f]")

EDIT_TOOL_NAMES = {"Edit", "MultiEdit", "Write", "NotebookEdit"}
INVESTIGATE_TOOLS = {"Read", "Glob", "Grep", "Agent", "Explore"}
VALIDATE_PATTERNS = ("test", "check", "build", "lint", "pytest", "vitest", "npm run")
COMMIT_PATTERNS = ("git add", "git commit", "git status")

IMPORTANT_OUTPUT_PATTERNS = (
    "error", "failed", "fatal", "panic", "exception",
    "traceback", "caused by", "operation not permitted",
)

# ---------------------------------------------------------------------------
# Teaching assistant content
# ---------------------------------------------------------------------------

PHASE_EXPLANATIONS = {
    "Investigating": "Reading files and searching code to understand what needs changing",
    "Coding": "Writing code changes based on what was learned",
    "Validating": "Running tests and type checks to make sure nothing broke",
    "Committing": "Saving changes to git so work isn\u2019t lost",
    "Complete": "All done \u2014 check the summary below",
}

TOOL_TIPS = {
    "Read": "Reading a file to understand its contents",
    "Glob": "Finding files by name pattern (like *.ts or **/*.svelte)",
    "Grep": "Searching for a text pattern across multiple files",
    "Edit": "Making a targeted change to a specific part of a file",
    "Write": "Creating or completely rewriting a file",
    "MultiEdit": "Making multiple changes to a file in one go",
    "Bash": "Running a shell command (tests, builds, git, etc.)",
    "Agent": "Launching a sub-agent to handle a complex task in parallel",
    "Explore": "Deeply exploring the codebase to find relevant code",
    "TodoWrite": "Creating or updating a task checklist",
    "NotebookEdit": "Editing a Jupyter notebook cell",
}

# Key project files — helps the user understand what was touched.
# Add your own project-specific files here for richer context in the dashboard.
FILE_CONTEXT = {
    "loop.sh": "Ralph automation loop \u2014 build/plan/coach/view modes",
    "render_coach_dashboard.py": "This dashboard renderer",
    "render_claude_stream.py": "Live transcript renderer for Claude streams",
    "CLAUDE.md": "Repo operating rules for Claude Code",
    "IMPLEMENTATION_PLAN.md": "Persistent execution state and task checklist",
    "PROMPT_plan.md": "Planning loop prompt",
    "PROMPT_build.md": "Build loop prompt",
    "PROMPT_coach.md": "Coach mode overlay prompt",
    "CHANGELOG.md": "Project change history",
    "README.md": "Project documentation",
}

# ---------------------------------------------------------------------------
# ANSI colours — disabled when stdout is not a TTY
# ---------------------------------------------------------------------------

USE_COLOR = sys.stdout.isatty()

RESET = "\033[0m" if USE_COLOR else ""
DIM = "\033[2m" if USE_COLOR else ""
BOLD = "\033[1m" if USE_COLOR else ""
RED = "\033[31m" if USE_COLOR else ""
GREEN = "\033[32m" if USE_COLOR else ""
YELLOW = "\033[33m" if USE_COLOR else ""
CYAN = "\033[36m" if USE_COLOR else ""
MAGENTA = "\033[35m" if USE_COLOR else ""


# ---------------------------------------------------------------------------
# Utility functions (replicated from render_claude_stream.py)
# ---------------------------------------------------------------------------

def strip_ansi(text: str) -> str:
    return ANSI_ESCAPE_RE.sub("", text)


def clean_text(text: str) -> str:
    return CONTROL_CHARS_RE.sub("", strip_ansi(text))


def compact(text: str, limit: int = 120) -> str:
    single_line = " ".join(clean_text(text).split())
    if len(single_line) <= limit:
        return single_line
    return f"{single_line[:limit - 3]}..."


def important_lines(text: str) -> list[str]:
    cleaned = [clean_text(line).rstrip() for line in text.splitlines()]
    non_empty = [line for line in cleaned if line.strip()]
    matches: list[str] = []
    for line in non_empty:
        lowered = line.lower()
        if any(p in lowered for p in IMPORTANT_OUTPUT_PATTERNS):
            if line not in matches:
                matches.append(line)
    return matches[:8] if matches else non_empty[-6:]


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
    if name == "Read":
        file_path = tool_input.get("file_path")
        if isinstance(file_path, str) and file_path.strip():
            return f"Read {file_path}"
    return name


def format_elapsed(seconds: float) -> str:
    mins, secs = divmod(int(seconds), 60)
    if mins > 0:
        return f"{mins}m {secs:02d}s"
    return f"{secs}s"


def term_width() -> int:
    return shutil.get_terminal_size((80, 24)).columns


# ---------------------------------------------------------------------------
# Phase detection
# ---------------------------------------------------------------------------

class Phase:
    INVESTIGATING = "Investigating"
    CODING = "Coding"
    VALIDATING = "Validating"
    COMMITTING = "Committing"
    COMPLETE = "Complete"

    ORDER = [INVESTIGATING, CODING, VALIDATING, COMMITTING, COMPLETE]
    NUMBERS = {
        INVESTIGATING: 1,
        CODING: 2,
        VALIDATING: 3,
        COMMITTING: 4,
        COMPLETE: 4,
    }


class PhaseDetector:
    def __init__(self) -> None:
        self.current = Phase.INVESTIGATING
        self._seen_edit = False

    def detect_from_tool(self, tool_name: str, tool_input: Any) -> str | None:
        """Return new phase name if the phase changed, else None."""
        cmd = ""
        if isinstance(tool_input, dict):
            cmd = str(tool_input.get("command", "")).lower()

        # Committing (only after we've seen edits)
        if self._seen_edit and tool_name == "Bash":
            if any(p in cmd for p in COMMIT_PATTERNS):
                return self._transition(Phase.COMMITTING)

        # Validating (only after we've seen edits)
        if self._seen_edit and tool_name == "Bash":
            if any(p in cmd for p in VALIDATE_PATTERNS):
                return self._transition(Phase.VALIDATING)

        # Coding
        if tool_name in EDIT_TOOL_NAMES:
            self._seen_edit = True
            return self._transition(Phase.CODING)

        # Investigating
        if tool_name in INVESTIGATE_TOOLS:
            # Only transition back to investigating if we haven't started coding
            if not self._seen_edit:
                return self._transition(Phase.INVESTIGATING)

        return None

    def mark_complete(self) -> str | None:
        return self._transition(Phase.COMPLETE)

    def _transition(self, new_phase: str) -> str | None:
        if new_phase != self.current:
            old = self.current
            self.current = new_phase
            return new_phase
        return None


# ---------------------------------------------------------------------------
# Spinner
# ---------------------------------------------------------------------------

class Spinner:
    def __init__(self) -> None:
        self._idx = 0

    def frame(self) -> str:
        ch = SPINNER_FRAMES[self._idx % len(SPINNER_FRAMES)]
        self._idx += 1
        return ch


# ---------------------------------------------------------------------------
# Terminal renderer
# ---------------------------------------------------------------------------

class TermRenderer:
    def __init__(self) -> None:
        self.spinner = Spinner()
        self._status_active = False

    def write(self, text: str) -> None:
        sys.stdout.write(text)
        sys.stdout.flush()

    def writeln(self, text: str = "") -> None:
        self.write(text + "\n")

    # --- Status line (overwritten in-place) ---

    def status_line(
        self, phase: str, ok: int, fail: int, files: int, elapsed: float
    ) -> None:
        spin = self.spinner.frame()
        elapsed_str = format_elapsed(elapsed)
        w = term_width()

        line = (
            f"  {CYAN}{spin}{RESET} {BOLD}{phase}...{RESET}"
            f"  {GREEN}\u2713{ok}{RESET}"
            f"  {RED}\u2717{fail}{RESET}"
            f"  {DIM}\u2206{files} files{RESET}"
            f"  {DIM}{elapsed_str}{RESET}"
        )

        # Truncate to terminal width (accounting for ANSI codes)
        self.write(f"\r\033[K{line}")
        self._status_active = True

    def clear_status(self) -> None:
        if self._status_active:
            self.write("\r\033[K")
            self._status_active = False

    # --- Banners ---

    def startup_banner(self, jsonl_path: str, is_live: bool) -> None:
        mode_label = "LIVE" if is_live else "REPLAY"
        mode_colour = GREEN if is_live else YELLOW
        inner = 56

        display_path = jsonl_path
        if len(display_path) > inner - 4:
            display_path = "..." + display_path[-(inner - 7):]

        def pad(visible_len: int) -> str:
            return " " * max(0, inner - visible_len - 2)

        self.writeln()
        self.writeln(f"  {CYAN}\u250f{'\u2501' * inner}\u2513{RESET}")
        self.writeln(f"  {CYAN}\u2503{RESET}  {BOLD}Ralph Coach Dashboard{RESET}{pad(21)}{CYAN}\u2503{RESET}")
        self.writeln(f"  {CYAN}\u2503{RESET}  {DIM}{display_path}{RESET}{pad(len(display_path))}{CYAN}\u2503{RESET}")
        self.writeln(f"  {CYAN}\u2503{RESET}  Mode: {mode_colour}{BOLD}{mode_label}{RESET}{pad(len(mode_label) + 6)}{CYAN}\u2503{RESET}")
        self.writeln(f"  {CYAN}\u2517{'\u2501' * inner}\u251b{RESET}")
        self.writeln()

    def phase_banner(self, phase: str, teaching: bool = False) -> None:
        step = Phase.NUMBERS.get(phase, 1)
        total = 4
        w = term_width()
        label = f" [{step}/{total}] {phase} "
        pad_len = max(0, w - len(label) - 6)
        self.writeln(f"\n  {BOLD}{CYAN}\u2501\u2501\u2501{label}{'\u2501' * pad_len}{RESET}")
        if teaching:
            explanation = PHASE_EXPLANATIONS.get(phase, "")
            if explanation:
                self.writeln(f"  {DIM}\U0001f4a1 {explanation}{RESET}")
                self.writeln()

    # --- Tool events ---

    def tool_start(self, label: str) -> None:
        self.writeln(f"  {DIM}\u2192 {compact(label)}{RESET}")

    def tool_ok(self, label: str, tool_name: str = "", teaching: bool = False) -> None:
        self.writeln(f"  {GREEN}\u2713{RESET} {compact(label)}")
        if teaching and tool_name:
            tip = TOOL_TIPS.get(tool_name, "")
            if tip:
                self.writeln(f"    {DIM}\u2514\u2500 {tip}{RESET}")

    def tool_fail(self, label: str, excerpt: list[str]) -> None:
        self.writeln(f"  {RED}\u2717{RESET} {BOLD}{compact(label)}{RESET}")
        for line in excerpt[:8]:
            self.writeln(f"    {RED}{line}{RESET}")

    # --- Labelled blocks (Insight / Checkpoint / Summary / Simple) ---

    def labeled_block(self, block_type: str, lines: list[str]) -> None:
        w = min(term_width() - 4, 56)
        header_pad = max(0, w - len(block_type) - 4)

        colour = CYAN
        if block_type == "Summary":
            colour = GREEN
        elif block_type == "Checkpoint":
            colour = YELLOW

        self.writeln(f"  {colour}\u250c\u2500 {BOLD}{block_type}{RESET}{colour} {'\u2500' * header_pad}{RESET}")
        for line in lines:
            self.writeln(f"  {colour}\u2502{RESET}  {line.rstrip()}")
        self.writeln(f"  {colour}\u2514{'\u2500' * (w + 1)}{RESET}")

    # --- Plan / TodoWrite ---

    def plan_block(self, items: list[tuple[str, str]]) -> None:
        """Render a TodoWrite checklist. items = [(status, content), ...]."""
        self.writeln(f"\n  {BOLD}{MAGENTA}\U0001f4cb Plan{RESET}")
        for status, content in items:
            marker = f"{GREEN}\u2713{RESET}" if status == "completed" else f"{DIM}\u25cb{RESET}"
            self.writeln(f"    {marker} {content}")
        self.writeln()

    # --- Agent text (not a labelled block) ---

    def agent_text(self, text: str) -> None:
        lines = text.strip().splitlines()
        for line in lines:
            self.writeln(f"  {DIM}{compact(line.rstrip(), 100)}{RESET}")

    # --- Tool breakdown chart ---

    def tool_breakdown(self, tool_counts: dict[str, int]) -> None:
        if not tool_counts:
            return
        sorted_tools = sorted(tool_counts.items(), key=lambda x: -x[1])
        max_count = sorted_tools[0][1] if sorted_tools else 1
        bar_width = 20

        self.writeln(f"\n  {BOLD}Tool Breakdown:{RESET}")
        for name, count in sorted_tools[:10]:
            filled = int((count / max_count) * bar_width)
            empty = bar_width - filled
            bar = f"{GREEN}\u2588{RESET}" * filled + f"{DIM}\u2591{RESET}" * empty
            self.writeln(f"    {name:<10s} {bar} {count}")
        self.writeln()

    # --- Phase timeline bar ---

    def phase_timeline(self, timestamps: list[tuple[str, float]], total_elapsed: float) -> None:
        if len(timestamps) < 2 or total_elapsed <= 0:
            return

        phase_colours = {
            Phase.INVESTIGATING: CYAN,
            Phase.CODING: MAGENTA,
            Phase.VALIDATING: YELLOW,
            Phase.COMMITTING: GREEN,
            Phase.COMPLETE: DIM,
        }

        # Aggregate durations per phase (phases can repeat, so sum them up)
        raw_durations: dict[str, float] = {}
        for i in range(len(timestamps)):
            phase_name = timestamps[i][0]
            start = timestamps[i][1]
            end = timestamps[i + 1][1] if i + 1 < len(timestamps) else timestamps[0][1] + total_elapsed
            raw_durations[phase_name] = raw_durations.get(phase_name, 0) + (end - start)

        # Order by the canonical phase order
        ordered: list[tuple[str, float]] = []
        for phase in Phase.ORDER:
            if phase in raw_durations and raw_durations[phase] > 0:
                ordered.append((phase, raw_durations[phase]))

        if not ordered:
            return

        bar_width = 40
        self.writeln(f"\n  {BOLD}Phase Timeline:{RESET}")

        bar_parts: list[str] = []
        label_parts: list[str] = []
        for phase_name, dur in ordered:
            pct = dur / total_elapsed if total_elapsed > 0 else 0
            width = max(1, int(pct * bar_width))
            colour = phase_colours.get(phase_name, DIM)
            bar_parts.append(f"{colour}{'\u2588' * width}{RESET}")
            label_parts.append(f"{colour}{phase_name} {int(pct * 100)}%{RESET}")

        self.writeln(f"    {''.join(bar_parts)}  {format_elapsed(total_elapsed)}")
        self.writeln(f"    {'  '.join(label_parts)}")
        self.writeln()

    # --- Cost & token summary ---

    def cost_summary(
        self, cost: float, input_tokens: int, output_tokens: int,
        cache_read: int, cache_write: int, num_turns: int,
        model_usage: dict[str, dict[str, int]]
    ) -> None:
        if cost <= 0 and output_tokens <= 0:
            return

        self.writeln(f"\n  {BOLD}Cost & Usage:{RESET}")
        if cost > 0:
            self.writeln(f"    Cost          {GREEN}${cost:.2f}{RESET}")
        total_tokens = input_tokens + output_tokens + cache_read + cache_write
        if total_tokens > 0:
            self.writeln(f"    Tokens        {total_tokens:,} total ({output_tokens:,} output, {cache_read:,} cache read)")
        if num_turns > 0:
            self.writeln(f"    Turns         {num_turns}")
        if model_usage:
            models = []
            for model, stats in sorted(model_usage.items()):
                out = stats.get("outputTokens", 0)
                if out > 0:
                    short = model.replace("claude-", "").replace("-4-6", " 4.6")
                    models.append(f"{short}: {out:,}")
            if models:
                self.writeln(f"    Models        {', '.join(models)}")
        self.writeln()

    # --- Summary box ---

    def summary_box(
        self,
        elapsed: float,
        tool_count: int,
        tool_ok: int,
        tool_fail: int,
        files_changed: set[str],
        phases: list[str],
        success: bool,
    ) -> None:
        inner = 56
        label_col = 16  # fixed column for values

        elapsed_str = format_elapsed(elapsed)
        result_label = "Success" if success else "Failed"
        result_str = f"{GREEN}{result_label}{RESET}" if success else f"{RED}{result_label}{RESET}"
        tools_str = f"{tool_count}  ({GREEN}\u2713{tool_ok}{RESET}  {RED}\u2717{tool_fail}{RESET})"
        phase_str = " \u2192 ".join(phases) if phases else "\u2014"

        if len(phase_str) > inner - label_col - 2:
            phase_str = phase_str[:inner - label_col - 5] + "..."

        border = GREEN if success else RED

        def row(label: str, value: str, visible_len: int | None = None) -> str:
            """Build a padded row. visible_len overrides len() for ANSI values."""
            if visible_len is None:
                visible_len = len(value)
            content = f"  {label}:{' ' * (label_col - len(label) - 1)} {value}"
            pad = max(0, inner - 2 - len(label) - (label_col - len(label) - 1) - 1 - visible_len)
            return f"  {border}\u2503{RESET}{content}{' ' * pad}{border}\u2503{RESET}"

        self.writeln(f"\n  {border}\u250f{'\u2501' * inner}\u2513{RESET}")
        self.writeln(f"  {border}\u2503{RESET}  {BOLD}Run Summary{RESET}{' ' * (inner - 13)}{border}\u2503{RESET}")
        self.writeln(f"  {border}\u2523{'\u2501' * inner}\u252b{RESET}")

        tools_visible = f"{tool_count}  (\u2713{tool_ok}  \u2717{tool_fail})"
        self.writeln(row("Duration", elapsed_str))
        self.writeln(row("Tools run", tools_str, len(tools_visible)))
        self.writeln(row("Files changed", str(len(files_changed))))
        self.writeln(row("Phases", phase_str))
        self.writeln(row("Result", result_str, len(result_label)))

        self.writeln(f"  {border}\u2517{'\u2501' * inner}\u251b{RESET}")

        if files_changed:
            self.writeln(f"\n  {BOLD}Changed files:{RESET}")
            for f in sorted(files_changed):
                basename = os.path.basename(f)
                context = FILE_CONTEXT.get(basename, "")
                if context:
                    self.writeln(f"    {f}  {DIM}\u2014 {context}{RESET}")
                else:
                    self.writeln(f"    {f}")

        self.writeln()

    def what_happened_block(
        self, files_changed: set[str], tool_count: int,
        tool_ok: int, tool_fail: int, phases: list[str]
    ) -> None:
        """Plain-English summary for ADHD-friendly quick scanning."""
        lines: list[str] = []

        if not phases:
            lines.append("Nothing happened \u2014 the run may have been interrupted early.")
        else:
            if "Coding" in phases:
                lines.append(f"\U0001f527 Made changes to {BOLD}{len(files_changed)}{RESET} file(s)")
            else:
                lines.append(f"\U0001f50d Investigated the codebase ({tool_count} tool calls)")

            if "Validating" in phases:
                if tool_fail > 0:
                    lines.append(f"\u26a0\ufe0f  Tests had {RED}{tool_fail} failure(s){RESET} \u2014 check the output above")
                else:
                    lines.append(f"\u2705 All checks passed")

            if "Committing" in phases:
                lines.append(f"\U0001f4be Changes committed to git and pushed")

        self.writeln(f"\n  {BOLD}{CYAN}\u250c\u2500 What Just Happened {'\u2500' * 35}{RESET}")
        for line in lines:
            self.writeln(f"  {CYAN}\u2502{RESET}  {line}")
        self.writeln(f"  {CYAN}\u2514{'\u2500' * 56}{RESET}")

    def what_to_review(self, files_changed: set[str]) -> None:
        """Suggest files the user should look at."""
        if not files_changed:
            return

        review_files: list[str] = []
        for f in sorted(files_changed):
            basename = os.path.basename(f)
            context = FILE_CONTEXT.get(basename, "")
            if context:
                review_files.append(f"  {basename}  {DIM}\u2014 {context}{RESET}")
            else:
                review_files.append(f"  {basename}")

        if not review_files:
            return

        self.writeln(f"\n  {BOLD}{YELLOW}\u250c\u2500 What to Review Next {'\u2500' * 34}{RESET}")
        self.writeln(f"  {YELLOW}\u2502{RESET}  Open these files to see what changed:")
        for rf in review_files[:8]:
            self.writeln(f"  {YELLOW}\u2502{RESET}    \u2022 {rf}")
        self.writeln(f"  {YELLOW}\u2514{'\u2500' * 56}{RESET}")
        self.writeln()


# ---------------------------------------------------------------------------
# Main dashboard
# ---------------------------------------------------------------------------

class CoachDashboard:
    def __init__(self, jsonl_path: str) -> None:
        self.jsonl_path = jsonl_path
        self.renderer = TermRenderer()
        self.detector = PhaseDetector()
        self.start_time = time.monotonic()
        self.tool_count = 0
        self.tool_ok_count = 0
        self.tool_fail_count = 0
        self.files_changed: set[str] = set()
        self.pending_tools: dict[str, str] = {}  # tool_id -> label
        self.pending_tool_names: dict[str, str] = {}  # tool_id -> tool_name
        self.run_complete = False
        self.run_success = False
        self.phase_history: list[str] = [Phase.INVESTIGATING]
        self._interrupted = False
        # Teaching mode: enabled when COACH_ITERATION env var is set (from loop.sh coach)
        self.teaching = bool(os.environ.get("COACH_ITERATION", ""))
        # Enhanced tracking for richer dashboard
        self.tool_name_counts: dict[str, int] = {}
        self.total_cost_usd: float = 0.0
        self.total_input_tokens: int = 0
        self.total_output_tokens: int = 0
        self.total_cache_read: int = 0
        self.total_cache_write: int = 0
        self.num_turns: int = 0
        self.duration_from_result: float = 0.0  # actual duration from result event (ms)
        self.model_usage: dict[str, dict[str, int]] = {}
        self.phase_timestamps: list[tuple[str, float]] = [(Phase.INVESTIGATING, time.monotonic())]

    def run(self) -> int:
        signal.signal(signal.SIGINT, self._handle_sigint)

        # Read all existing lines
        with open(self.jsonl_path, "r") as fh:
            existing = fh.readlines()

        is_complete = self._check_complete(existing)
        is_live = not is_complete

        self.renderer.startup_banner(self.jsonl_path, is_live)

        # Show iteration progress if in coach mode
        coach_iter = os.environ.get("COACH_ITERATION", "")
        coach_total = os.environ.get("COACH_TOTAL", "")
        if coach_iter and coach_total:
            self.renderer.writeln(
                f"  {BOLD}\U0001f3c3 Iteration {coach_iter}/{coach_total}{RESET}"
            )
            self.renderer.writeln()

        # First phase banner
        self.renderer.phase_banner(Phase.INVESTIGATING, teaching=self.teaching)

        # Process existing events
        for line in existing:
            self._process_line(line)

        if is_complete or self._interrupted:
            self._print_summary()
            return 0

        # Live tail mode — seek to end and poll for new lines
        with open(self.jsonl_path, "r") as fh:
            fh.seek(0, 2)  # seek to end
            while not self.run_complete and not self._interrupted:
                line = fh.readline()
                if line:
                    self.renderer.clear_status()
                    self._process_line(line)
                else:
                    elapsed = time.monotonic() - self.start_time
                    self.renderer.status_line(
                        self.detector.current,
                        self.tool_ok_count,
                        self.tool_fail_count,
                        len(self.files_changed),
                        elapsed,
                    )
                    time.sleep(POLL_INTERVAL)

        self.renderer.clear_status()
        self._print_summary()
        return 0

    # --- Event processing ---

    def _check_complete(self, lines: list[str]) -> bool:
        for line in reversed(lines):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                event = json.loads(stripped)
                return event.get("type") == "result"
            except json.JSONDecodeError:
                continue
        return False

    def _process_line(self, raw_line: str) -> None:
        stripped = raw_line.strip()
        if not stripped:
            return
        try:
            event = json.loads(stripped)
        except json.JSONDecodeError:
            return
        if isinstance(event, dict):
            self._process_event(event)

    def _process_event(self, event: dict[str, Any]) -> None:
        event_type = event.get("type")

        # Handle message wrapper
        message = event.get("message")
        if isinstance(message, dict):
            self._process_message(message)
            return

        if event_type == "result":
            self._handle_result(event)
            return

        if event_type in ("assistant", "user"):
            self._process_message(event)
            return

        if event_type == "error":
            msg = event.get("message") or event.get("error") or "Unknown error"
            self.renderer.writeln(f"  {RED}\u2717 ERROR: {clean_text(str(msg))}{RESET}")

    def _process_message(self, message: dict[str, Any]) -> None:
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
                    self._handle_text(clean_text(text))

            elif block_type == "tool_use":
                self._handle_tool_use(block)

            elif block_type == "tool_result":
                self._handle_tool_result(block)

    def _handle_text(self, text: str) -> None:
        stripped = text.strip()
        if not stripped:
            return

        lines = [line.rstrip() for line in stripped.splitlines() if line.strip()]
        if not lines:
            return

        heading = lines[0].rstrip(":").lower()

        # Detect labelled blocks from coach/homer overlay
        if heading in ("insight", "checkpoint", "summary", "simple"):
            block_type = heading.capitalize()
            body = [line for line in lines[1:]]
            self.renderer.labeled_block(block_type, body)
            return

        # Regular agent text — show briefly
        self.renderer.agent_text(stripped)

    def _handle_tool_use(self, block: dict[str, Any]) -> None:
        tool_name = str(block.get("name", "")).strip()
        tool_input = block.get("input")
        tool_id = str(block.get("id", "")).strip()

        # TodoWrite gets special treatment
        if tool_name == "TodoWrite" and self._render_todo_write(tool_input):
            if tool_id:
                self.pending_tools[tool_id] = "TodoWrite"
            return

        # Track changed files
        if tool_name in EDIT_TOOL_NAMES and isinstance(tool_input, dict):
            fp = tool_input.get("file_path")
            if isinstance(fp, str) and fp.strip():
                self.files_changed.add(fp)

        # Phase detection
        new_phase = self.detector.detect_from_tool(tool_name, tool_input)
        if new_phase and new_phase != Phase.COMPLETE:
            if new_phase not in self.phase_history:
                self.phase_history.append(new_phase)
            self.phase_timestamps.append((new_phase, time.monotonic()))
            self.renderer.phase_banner(new_phase, teaching=self.teaching)

        label = command_from_tool_input(tool_name or "tool", tool_input)
        self.tool_count += 1
        if tool_name:
            self.tool_name_counts[tool_name] = self.tool_name_counts.get(tool_name, 0) + 1

        if tool_id:
            self.pending_tools[tool_id] = label
            self.pending_tool_names[tool_id] = tool_name

    def _handle_tool_result(self, block: dict[str, Any]) -> None:
        tool_id = str(block.get("tool_use_id", "")).strip()
        label = self.pending_tools.pop(tool_id, "tool")
        tool_name = self.pending_tool_names.pop(tool_id, "")
        is_error = bool(block.get("is_error"))
        output = extract_text(block.get("content", ""))

        if is_error:
            self.tool_fail_count += 1
            excerpt = important_lines(output)
            self.renderer.tool_fail(label, excerpt)
        else:
            self.tool_ok_count += 1
            self.renderer.tool_ok(label, tool_name=tool_name, teaching=self.teaching)

    def _handle_result(self, event: dict[str, Any]) -> None:
        self.run_complete = True
        self.run_success = event.get("subtype") == "success"
        self.detector.mark_complete()

        # Extract real cost/usage data from result events
        cost = event.get("total_cost_usd")
        if isinstance(cost, (int, float)):
            self.total_cost_usd += cost
        turns = event.get("num_turns")
        if isinstance(turns, int):
            self.num_turns += turns
        dur = event.get("duration_ms")
        if isinstance(dur, (int, float)):
            self.duration_from_result += dur
        usage = event.get("usage")
        if isinstance(usage, dict):
            self.total_input_tokens += usage.get("input_tokens", 0)
            self.total_output_tokens += usage.get("output_tokens", 0)
            self.total_cache_read += usage.get("cache_read_input_tokens", 0)
            self.total_cache_write += usage.get("cache_creation_input_tokens", 0)
        model_usage = event.get("modelUsage")
        if isinstance(model_usage, dict):
            for model, stats in model_usage.items():
                if isinstance(stats, dict):
                    existing = self.model_usage.get(model, {})
                    for k, v in stats.items():
                        if isinstance(v, int):
                            existing[k] = existing.get(k, 0) + v
                    self.model_usage[model] = existing

        if not self.run_success:
            result_text = event.get("result")
            if isinstance(result_text, str) and result_text.strip():
                self.renderer.writeln(f"\n  {RED}\u2717 Run ended with error:{RESET}")
                for line in important_lines(result_text):
                    self.renderer.writeln(f"    {RED}{line}{RESET}")

    def _render_todo_write(self, tool_input: Any) -> bool:
        if not isinstance(tool_input, dict):
            return False
        todos = tool_input.get("todos")
        if not isinstance(todos, list):
            return False

        items: list[tuple[str, str]] = []
        for todo in todos:
            if not isinstance(todo, dict):
                continue
            status = todo.get("status", "")
            content = todo.get("content") or todo.get("text") or ""
            items.append((status, content))

        if items:
            self.renderer.plan_block(items)
            return True
        return False

    def _print_summary(self) -> None:
        elapsed = time.monotonic() - self.start_time
        # Prefer actual duration from the JSONL result event (accurate for replays)
        if self.duration_from_result > 0:
            elapsed = self.duration_from_result / 1000.0

        # Teaching mode: plain-English summary first
        if self.teaching:
            self.renderer.what_happened_block(
                files_changed=self.files_changed,
                tool_count=self.tool_count,
                tool_ok=self.tool_ok_count,
                tool_fail=self.tool_fail_count,
                phases=self.phase_history,
            )

        self.renderer.summary_box(
            elapsed=elapsed,
            tool_count=self.tool_count,
            tool_ok=self.tool_ok_count,
            tool_fail=self.tool_fail_count,
            files_changed=self.files_changed,
            phases=self.phase_history,
            success=self.run_success if self.run_complete else False,
        )

        # Tool breakdown chart
        self.renderer.tool_breakdown(self.tool_name_counts)

        # Phase timeline
        self.renderer.phase_timeline(self.phase_timestamps, elapsed)

        # Cost & token summary
        self.renderer.cost_summary(
            cost=self.total_cost_usd,
            input_tokens=self.total_input_tokens,
            output_tokens=self.total_output_tokens,
            cache_read=self.total_cache_read,
            cache_write=self.total_cache_write,
            num_turns=self.num_turns,
            model_usage=self.model_usage,
        )

        # Teaching mode: suggest files to review
        if self.teaching:
            self.renderer.what_to_review(self.files_changed)

    def _handle_sigint(self, sig: int, frame: Any) -> None:
        self._interrupted = True
        self.renderer.clear_status()
        self.renderer.writeln(f"\n  {YELLOW}Interrupted \u2014 showing partial summary.{RESET}")
        self._print_summary()
        sys.exit(0)


# ---------------------------------------------------------------------------
# Quick JSONL parser for multi-run summaries
# ---------------------------------------------------------------------------

def quick_parse_jsonl(path: str) -> dict[str, Any]:
    """Fast parse a JSONL file for summary stats without rendering."""
    stats: dict[str, Any] = {
        "path": path,
        "mode": "build",
        "timestamp": "",
        "tool_count": 0,
        "tool_ok": 0,
        "tool_fail": 0,
        "files_changed": set(),
        "success": False,
        "complete": False,
        "cost_usd": 0.0,
        "duration_ms": 0,
        "num_turns": 0,
        "tool_names": {},
    }

    basename = os.path.basename(path)
    if basename.startswith("coach-"):
        stats["mode"] = "coach"
    elif basename.startswith("plan-"):
        stats["mode"] = "plan"

    # Extract timestamp from filename (e.g., coach-20260320-071152.jsonl)
    ts_match = re.search(r"(\d{8})-(\d{6})", basename)
    if ts_match:
        d, t = ts_match.groups()
        stats["timestamp"] = f"{d[6:8]}/{d[4:6]} {t[0:2]}:{t[2:4]}"

    try:
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue

                # Count tools
                msg = ev.get("message") if isinstance(ev.get("message"), dict) else ev
                content = msg.get("content") if isinstance(msg, dict) else None
                if isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict):
                            if block.get("type") == "tool_use":
                                stats["tool_count"] += 1
                                name = block.get("name", "")
                                stats["tool_names"][name] = stats["tool_names"].get(name, 0) + 1
                                inp = block.get("input", {})
                                if name in EDIT_TOOL_NAMES and isinstance(inp, dict):
                                    fp = inp.get("file_path", "")
                                    if fp:
                                        stats["files_changed"].add(fp)
                            elif block.get("type") == "tool_result":
                                if block.get("is_error"):
                                    stats["tool_fail"] += 1
                                else:
                                    stats["tool_ok"] += 1

                if ev.get("type") == "result":
                    stats["complete"] = True
                    stats["success"] = ev.get("subtype") == "success"
                    cost = ev.get("total_cost_usd")
                    if isinstance(cost, (int, float)):
                        stats["cost_usd"] += cost
                    dur = ev.get("duration_ms")
                    if isinstance(dur, (int, float)):
                        stats["duration_ms"] += dur
                    turns = ev.get("num_turns")
                    if isinstance(turns, int):
                        stats["num_turns"] += turns
    except OSError:
        pass

    return stats


# ---------------------------------------------------------------------------
# Multi-run viewer
# ---------------------------------------------------------------------------

class MultiRunViewer:
    """Renders a comparison grid of multiple JSONL runs."""

    def __init__(self, run_dir: str, last_n: int = 0) -> None:
        self.run_dir = run_dir
        self.last_n = last_n
        self.renderer = TermRenderer()

    def run(self) -> int:
        jsonl_files = sorted(
            [os.path.join(self.run_dir, f) for f in os.listdir(self.run_dir) if f.endswith(".jsonl")],
            key=lambda p: os.path.getmtime(p),
            reverse=True,
        )

        if not jsonl_files:
            print("No JSONL files found in .claude-run/", file=sys.stderr)
            return 1

        if self.last_n > 0:
            jsonl_files = jsonl_files[:self.last_n]

        # Quick-parse all runs — only show completed ones in "past" view
        runs = [r for r in (quick_parse_jsonl(p) for p in jsonl_files) if r["complete"]]

        if not runs:
            print("No completed runs found in .claude-run/", file=sys.stderr)
            return 1

        self._render_grid(runs)
        self._render_file_heatmap(runs)
        self._render_totals(runs)

        # Quick summary of the latest completed run
        latest = runs[0]
        changed = sorted(latest["files_changed"])
        basenames = [os.path.basename(f) for f in changed[:6]]
        self.renderer.writeln(f"  {BOLD}Latest run:{RESET} {latest['timestamp']} — "
                              f"{latest['tool_ok']} tools, "
                              f"{len(latest['files_changed'])} files, "
                              f"${latest['cost_usd']:.2f}")
        if basenames:
            self.renderer.writeln(f"    Changed: {', '.join(basenames)}")
        self.renderer.writeln()

        # Interactive selection
        self.renderer.writeln(f"  {BOLD}Enter run # to expand (or q to quit):{RESET} ")
        try:
            choice = input("  > ").strip()
        except (EOFError, KeyboardInterrupt):
            return 0

        if choice.lower() in ("q", "quit", ""):
            return 0

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(runs):
                self.renderer.writeln()
                dashboard = CoachDashboard(runs[idx]["path"])
                dashboard.teaching = True
                return dashboard.run()
            else:
                print(f"Invalid selection: {choice}", file=sys.stderr)
                return 1
        except ValueError:
            print(f"Invalid selection: {choice}", file=sys.stderr)
            return 1

    def _render_grid(self, runs: list[dict[str, Any]]) -> None:
        mode_colours = {"coach": CYAN, "build": GREEN, "plan": YELLOW}

        self.renderer.writeln()
        self.renderer.writeln(f"  {CYAN}\u250f{'━' * 78}\u2513{RESET}")
        title = f"Last {len(runs)} Runs" if self.last_n > 0 else f"All {len(runs)} Runs"
        self.renderer.writeln(f"  {CYAN}\u2503{RESET}  {BOLD}{title}{RESET}{' ' * (74 - len(title))}{CYAN}\u2503{RESET}")
        self.renderer.writeln(f"  {CYAN}\u2523{'━' * 78}\u252b{RESET}")

        header = (
            f"  {CYAN}\u2503{RESET}"
            f"  {DIM}{'#':>3}{RESET}"
            f"  {DIM}{'Timestamp':<14}{RESET}"
            f"  {DIM}{'Mode':<7}{RESET}"
            f"  {DIM}{'Tools':>6}{RESET}"
            f"  {DIM}{'Files':>5}{RESET}"
            f"  {DIM}{'Time':>7}{RESET}"
            f"  {DIM}{'Cost':>8}{RESET}"
            f"  {DIM}{'Turns':>5}{RESET}"
            f"  {DIM}{'Result':<8}{RESET}"
            f"  {CYAN}\u2503{RESET}"
        )
        self.renderer.writeln(header)
        self.renderer.writeln(f"  {CYAN}\u2523{'━' * 78}\u252b{RESET}")

        for i, run in enumerate(runs):
            mc = mode_colours.get(run["mode"], DIM)
            dur = format_elapsed(run["duration_ms"] / 1000) if run["duration_ms"] > 0 else "—"
            cost = f"${run['cost_usd']:.2f}" if run["cost_usd"] > 0 else "—"
            result_str = f"{GREEN}\u2713{RESET}" if run["success"] else (f"{RED}\u2717{RESET}" if run["complete"] else f"{DIM}\u2026{RESET}")
            tools_str = f"\u2713{run['tool_ok']}"

            # Alternate row shading
            shade = DIM if i % 2 == 1 else ""
            end_shade = RESET if shade else ""

            row = (
                f"  {CYAN}\u2503{RESET}"
                f"  {shade}{i + 1:>3}{end_shade}"
                f"  {shade}{run['timestamp']:<14}{end_shade}"
                f"  {mc}{run['mode']:<7}{RESET}"
                f"  {shade}{tools_str:>6}{end_shade}"
                f"  {shade}{len(run['files_changed']):>5}{end_shade}"
                f"  {shade}{dur:>7}{end_shade}"
                f"  {shade}{cost:>8}{end_shade}"
                f"  {shade}{run['num_turns']:>5}{end_shade}"
                f"  {result_str:<8}"
                f"  {CYAN}\u2503{RESET}"
            )
            self.renderer.writeln(row)

        self.renderer.writeln(f"  {CYAN}\u2517{'━' * 78}\u251b{RESET}")
        self.renderer.writeln()

    def _render_file_heatmap(self, runs: list[dict[str, Any]]) -> None:
        """Show files that changed most frequently across runs."""
        file_counts: dict[str, int] = {}
        for run in runs:
            for f in run["files_changed"]:
                basename = os.path.basename(f)
                file_counts[basename] = file_counts.get(basename, 0) + 1

        if not file_counts:
            return

        sorted_files = sorted(file_counts.items(), key=lambda x: -x[1])[:10]
        max_count = sorted_files[0][1]
        total = len(runs)
        bar_width = 12

        self.renderer.writeln(f"  {BOLD}Frequently Changed Files ({len(runs)} runs):{RESET}")
        for basename, count in sorted_files:
            filled = int((count / max_count) * bar_width)
            empty = bar_width - filled
            bar = f"{MAGENTA}\u2588{RESET}" * filled + f"{DIM}\u2591{RESET}" * empty
            context = FILE_CONTEXT.get(basename, "")
            ctx_str = f"  {DIM}\u2014 {context}{RESET}" if context else ""
            self.renderer.writeln(f"    {basename:<30s} {bar} {count}/{total}{ctx_str}")
        self.renderer.writeln()

    def _render_totals(self, runs: list[dict[str, Any]]) -> None:
        """Grand totals across all displayed runs."""
        total_cost = sum(r["cost_usd"] for r in runs)
        total_tools = sum(r["tool_ok"] for r in runs)
        total_files = len(set().union(*(r["files_changed"] for r in runs)))
        total_dur = sum(r["duration_ms"] for r in runs)
        successes = sum(1 for r in runs if r["success"])

        self.renderer.writeln(f"  {BOLD}Totals:{RESET}")
        self.renderer.writeln(
            f"    {GREEN}${total_cost:.2f}{RESET} spent"
            f"  \u2502  {total_tools} tools"
            f"  \u2502  {total_files} files"
            f"  \u2502  {format_elapsed(total_dur / 1000)}"
            f"  \u2502  {successes}/{len(runs)} succeeded"
        )
        self.renderer.writeln()


# ---------------------------------------------------------------------------
# Follow viewer — live session monitor
# ---------------------------------------------------------------------------

class FollowViewer:
    """Watches .claude-run/ for new JSONL files and shows live dashboards.

    Designed to run alongside any loop mode (plan, build, coach) in a
    second terminal. Follows iterations as they happen, accumulates stats,
    and exits when the session goes idle (no new files for IDLE_TIMEOUT).
    """

    POLL_SECONDS = 2.0
    IDLE_TIMEOUT = 30.0  # seconds with no new file before assuming session ended

    def __init__(self, run_dir: str) -> None:
        self.run_dir = run_dir
        self.renderer = TermRenderer()
        self.completed: list[dict[str, Any]] = []
        self._interrupted = False

    def run(self) -> int:
        signal.signal(signal.SIGINT, self._handle_sigint)
        self._banner()

        seen_files: set[str] = set()
        # Mark all existing files as "before this session" so we only follow new ones
        initial_files = self._list_jsonl_files()
        # Keep the most recent file if it's still incomplete — we'll tail it
        if initial_files:
            latest = initial_files[0]
            if not self._is_complete(latest):
                seen_files = set(initial_files[1:])
            else:
                seen_files = set(initial_files)

        while not self._interrupted:
            latest = self._find_latest_new(seen_files)

            if latest is None:
                # Wait for a new file, but give up after IDLE_TIMEOUT
                found = self._wait_for_new_file(seen_files)
                if not found:
                    # Idle timeout — session is over
                    break
                continue

            seen_files.add(latest)
            iteration = len(self.completed) + 1

            self.renderer.writeln(
                f"\n  {BOLD}{CYAN}\u2501\u2501\u2501 Iteration "
                f"{iteration} \u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501"
                f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501"
                f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501"
                f"\u2501\u2501{RESET}"
            )

            # Show live dashboard — blocks until the JSONL gets a result event
            dashboard = CoachDashboard(latest)
            dashboard.teaching = True
            dashboard.run()

            # Quick-parse for grid stats
            stats = quick_parse_jsonl(latest)
            self.completed.append(stats)

            # Show running grid between iterations
            self._render_running_grid()

        # Final summary
        if self.completed:
            self._render_final()
        else:
            self.renderer.writeln(
                f"\n  {DIM}No iterations observed. "
                f"Start a loop in another terminal:{RESET}"
            )
            self.renderer.writeln(
                f"    ./loop.sh coach 5   or   ./loop.sh plan 3   or   ./loop.sh 10"
            )
            self.renderer.writeln()
        return 0

    def _list_jsonl_files(self) -> list[str]:
        """Return all JSONL files in run_dir, newest first."""
        try:
            files = [
                os.path.join(self.run_dir, f)
                for f in os.listdir(self.run_dir)
                if f.endswith(".jsonl")
            ]
            return sorted(files, key=lambda p: os.path.getmtime(p), reverse=True)
        except OSError:
            return []

    def _is_complete(self, path: str) -> bool:
        """Check if a JSONL file has a result event (i.e., the run finished)."""
        try:
            with open(path, "r") as f:
                for line in reversed(f.readlines()[-20:]):
                    stripped = line.strip()
                    if not stripped:
                        continue
                    try:
                        ev = json.loads(stripped)
                        if ev.get("type") == "result":
                            return True
                    except json.JSONDecodeError:
                        continue
        except OSError:
            pass
        return False

    def _find_latest_new(self, seen: set[str]) -> str | None:
        """Find the newest JSONL file not in the seen set."""
        for path in self._list_jsonl_files():
            if path not in seen:
                return path
        return None

    def _wait_for_new_file(self, seen: set[str]) -> bool:
        """Poll for a new JSONL file with a spinner. Returns False on idle timeout."""
        iteration = len(self.completed) + 1
        spinner = Spinner()
        waited = 0.0
        # First wait is longer (initial startup) — subsequent waits use IDLE_TIMEOUT
        timeout = 120.0 if not self.completed else self.IDLE_TIMEOUT
        while not self._interrupted and waited < timeout:
            new = self._find_latest_new(seen)
            if new is not None:
                self.renderer.clear_status()
                return True
            spin = spinner.frame()
            label = "Waiting for next iteration..." if self.completed else "Waiting for loop to start..."
            self.renderer.write(f"\r\033[K  {CYAN}{spin}{RESET} {label}")
            time.sleep(self.POLL_SECONDS)
            waited += self.POLL_SECONDS
        self.renderer.clear_status()
        if self.completed:
            self.renderer.writeln(
                f"\n  {DIM}No new iteration for {int(timeout)}s — session appears complete.{RESET}"
            )
        return False

    def _banner(self) -> None:
        inner = 56
        self.renderer.writeln()
        self.renderer.writeln(f"  {GREEN}\u250f{'\u2501' * inner}\u2513{RESET}")
        self.renderer.writeln(
            f"  {GREEN}\u2503{RESET}  {BOLD}Ralph Live Monitor{RESET}"
            f"{' ' * (inner - 20)}{GREEN}\u2503{RESET}"
        )
        self.renderer.writeln(
            f"  {GREEN}\u2503{RESET}  {DIM}Following current session in .claude-run/{RESET}"
            f"{' ' * max(0, inner - 43)}{GREEN}\u2503{RESET}"
        )
        self.renderer.writeln(
            f"  {GREEN}\u2503{RESET}  {DIM}Ctrl+C to stop early{RESET}"
            f"{' ' * (inner - 22)}{GREEN}\u2503{RESET}"
        )
        self.renderer.writeln(f"  {GREEN}\u2517{'\u2501' * inner}\u251b{RESET}")
        self.renderer.writeln()

    def _render_running_grid(self) -> None:
        """Show accumulated stats so far."""
        if not self.completed:
            return

        viewer = MultiRunViewer.__new__(MultiRunViewer)
        viewer.run_dir = self.run_dir
        viewer.last_n = len(self.completed)
        viewer.renderer = self.renderer

        viewer._render_grid(self.completed)
        viewer._render_totals(self.completed)

    def _render_final(self) -> None:
        """Full final summary with grid + heatmap + totals."""
        viewer = MultiRunViewer.__new__(MultiRunViewer)
        viewer.run_dir = self.run_dir
        viewer.last_n = len(self.completed)
        viewer.renderer = self.renderer

        self.renderer.writeln(
            f"\n  {GREEN}{BOLD}\u2501\u2501\u2501 Session Complete "
            f"({len(self.completed)} iterations) "
            f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501"
            f"\u2501\u2501\u2501\u2501{RESET}"
        )

        viewer._render_grid(self.completed)
        viewer._render_file_heatmap(self.completed)
        viewer._render_totals(self.completed)

    def _handle_sigint(self, sig: int, frame: Any) -> None:
        self._interrupted = True
        self.renderer.clear_status()
        self.renderer.writeln(
            f"\n  {YELLOW}Interrupted \u2014 showing partial summary.{RESET}"
        )
        if self.completed:
            self._render_final()
        sys.exit(0)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    args = sys.argv[1:]

    # Parse --future, --last N, --pick, --dir <path>
    last_n = 0
    future_mode = False
    run_dir = ".claude-run"
    pick_mode = False
    jsonl_path = None

    i = 0
    while i < len(args):
        if args[i] == "--last" and i + 1 < len(args):
            try:
                last_n = int(args[i + 1])
            except ValueError:
                pass
            i += 2
        elif args[i] == "--future":
            future_mode = True
            i += 1
        elif args[i] == "--pick":
            pick_mode = True
            i += 1
        elif args[i] == "--dir" and i + 1 < len(args):
            run_dir = args[i + 1]
            i += 2
        elif not args[i].startswith("-"):
            jsonl_path = args[i]
            i += 1
        else:
            i += 1

    # Future mode (live session monitor — follows until idle)
    if future_mode:
        viewer = FollowViewer(run_dir)
        return viewer.run()

    # Multi-run mode (--last N or --pick)
    if last_n > 0 or pick_mode:
        viewer = MultiRunViewer(run_dir, last_n=last_n)
        return viewer.run()

    # Single-run mode
    if not jsonl_path:
        print("Usage: render_coach_dashboard.py <jsonl_path>", file=sys.stderr)
        print("       render_coach_dashboard.py --future --dir <run_dir>", file=sys.stderr)
        print("       render_coach_dashboard.py --pick --dir <run_dir>", file=sys.stderr)
        return 1

    if not os.path.isfile(jsonl_path):
        print(f"File not found: {jsonl_path}", file=sys.stderr)
        return 1

    dashboard = CoachDashboard(jsonl_path)
    return dashboard.run()


if __name__ == "__main__":
    raise SystemExit(main())
