#!/usr/bin/env bash
set -euo pipefail

# Ralph loop wrapper for Claude Code
# Usage:
#   ./loop-claude.sh plan [N]                    Plan mode (N iterations, default unlimited)
#   ./loop-claude.sh build [N] [coach|homer]     Build mode with optional teaching overlay
#   ./loop-claude.sh coach [N]                   Coach mode: build + dashboard after each iteration
#   ./loop-claude.sh view past                   Browse completed runs — interactive grid picker
#   ./loop-claude.sh view future                 Follow the current loop live until it stops
#   ./loop-claude.sh view .claude-run/file.jsonl Replay a specific run
#   ./loop-claude.sh view                        Show view help
#
# Environment variables:
#   RALPH_EXPLAIN_MODE=coach|homer        Override explain mode
#   RALPH_ALLOW_UNSAFE_PERMISSIONS=1      Auto-approve all tool calls (YOLO mode)
#   RALPH_OUTPUT_MODE=json                Raw JSON output instead of pretty rendering
#   RALPH_MAX_TURNS=N                     Limit Claude turns per iteration

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_DIR="$SCRIPT_DIR/.claude-run"
DASHBOARD_RENDERER="$SCRIPT_DIR/scripts/render_coach_dashboard.py"

# ── View mode ────────────────────────────────────────────────
if [[ "${1:-}" == "view" ]]; then
    if [[ ! -d "$RUN_DIR" ]]; then
        echo "No .claude-run/ directory found — run a build or plan first."
        exit 1
    fi
    # Explicit file path — replay it directly
    if [[ -n "${2:-}" ]] && [[ -f "${2:-}" ]]; then
        exec python3 "$DASHBOARD_RENDERER" "$2"
    fi
    # past — browse completed runs
    if [[ "${2:-}" == "past" ]]; then
        exec python3 "$DASHBOARD_RENDERER" --pick --dir "$RUN_DIR"
    fi
    # future — follow the current loop live until it stops
    if [[ "${2:-}" == "future" ]]; then
        exec python3 "$DASHBOARD_RENDERER" --future --dir "$RUN_DIR"
    fi
    # No arg or unrecognised — show help
    echo ""
    echo "  Usage:"
    echo "    ./loop-claude.sh view past                                    Browse completed runs"
    echo "    ./loop-claude.sh view future                                  Follow the current loop live"
    echo "    ./loop-claude.sh view .claude-run/coach-20260320-124912.jsonl  Replay a specific run"
    echo ""
    exit 0
fi

# ── Coach mode (build iterations + dashboard after each) ─────
if [[ "${1:-}" == "coach" ]]; then
    # If second arg is an existing file, just view it (backwards compat)
    if [[ -n "${2:-}" ]] && [[ -f "${2:-}" ]]; then
        exec python3 "$DASHBOARD_RENDERER" "$2"
    fi

    MAX_COACH=${2:-1}
    mkdir -p "$RUN_DIR"
    CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "detached-head")
    PROMPT_FILE="PROMPT_build.md"

    if [[ ! -f "$PROMPT_FILE" ]]; then
        echo "Error: $PROMPT_FILE not found"
        exit 1
    fi

    echo ""
    echo "  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓"
    echo "  ┃  Coach Mode                                    ┃"
    echo "  ┃  Build + Learn — see what Ralph does and why   ┃"
    echo "  ┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫"
    echo "  ┃  Branch:     $CURRENT_BRANCH"
    echo "  ┃  Iterations: $MAX_COACH"
    echo "  ┃  Prompt:     $PROMPT_FILE"
    echo "  ┃  Logs:       .claude-run/"
    echo "  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛"
    echo ""

    for i in $(seq 1 "$MAX_COACH"); do
        echo ""
        echo "  ━━━ Coach iteration $i/$MAX_COACH ━━━━━━━━━━━━━━━━━━━━━━"
        echo ""

        TIMESTAMP=$(date +%Y%m%d-%H%M%S)
        JSONL_FILE="$RUN_DIR/coach-${TIMESTAMP}.jsonl"

        cat "$PROMPT_FILE" | claude -p \
            --dangerously-skip-permissions \
            --output-format=stream-json \
            --verbose \
        | tee "$JSONL_FILE"

        echo ""
        echo "  ━━━ Dashboard for iteration $i/$MAX_COACH ━━━━━━━━━━━━━"
        echo ""

        # Show the coach dashboard for this iteration
        COACH_ITERATION="$i" COACH_TOTAL="$MAX_COACH" \
            python3 "$DASHBOARD_RENDERER" "$JSONL_FILE"

        if [[ "$i" -lt "$MAX_COACH" ]]; then
            echo ""
            echo "  Starting next iteration in 3 seconds... (Ctrl+C to stop)"
            sleep 3
        fi
    done

    echo ""
    echo "  Coach mode complete — $MAX_COACH iteration(s) finished."
    echo "  Logs saved to .claude-run/coach-*.jsonl"
    echo "  Review any run: ./loop-claude.sh view past"
    echo ""
    exit 0
fi

# ── Parse build/plan arguments ──────────────────────────────
MODE="${1:-build}"
MAX_ITERATIONS="${2:-0}"
EXPLAIN_MODE="${RALPH_EXPLAIN_MODE:-}"
ALLOW_UNSAFE_PERMISSIONS="${RALPH_ALLOW_UNSAFE_PERMISSIONS:-0}"
OUTPUT_MODE="${RALPH_OUTPUT_MODE:-pretty}"
MAX_TURNS="${RALPH_MAX_TURNS:-}"

if [[ "${2:-}" == "coach" || "${2:-}" == "homer" ]]; then
    MAX_ITERATIONS="0"
    EXPLAIN_MODE="${2:-}"
fi

if [[ "${3:-}" == "coach" || "${3:-}" == "homer" ]]; then
    EXPLAIN_MODE="${3:-}"
fi

case "$MODE" in
    plan)
        PROMPT_FILE="PROMPT_plan.md"
        ;;
    build)
        PROMPT_FILE="PROMPT_build.md"
        ;;
    *)
        if [[ "$MODE" =~ ^[0-9]+$ ]]; then
            PROMPT_FILE="PROMPT_build.md"
            MAX_ITERATIONS="$MODE"
            MODE="build"
        else
            echo "Usage: ./loop-claude.sh [plan|build|coach|view] [max_iterations] [coach|homer]"
            exit 1
        fi
        ;;
esac

if [[ ! -f "$PROMPT_FILE" ]]; then
    echo "Missing prompt file: $PROMPT_FILE"
    exit 1
fi

if ! git rev-parse --show-toplevel >/dev/null 2>&1; then
    echo "This loop expects to run inside a git repository."
    exit 1
fi

mkdir -p "$RUN_DIR"
RENDERER="scripts/render_claude_stream.py"
EXTRACTOR="scripts/extract_claude_final.py"
OVERLAY_PROMPT_FILE=""

if [[ "$EXPLAIN_MODE" == "coach" ]]; then
    OVERLAY_PROMPT_FILE="PROMPT_coach.md"
elif [[ "$EXPLAIN_MODE" == "homer" ]]; then
    OVERLAY_PROMPT_FILE="PROMPT_homer.md"
fi

ITERATION=0
BRANCH="$(git branch --show-current 2>/dev/null || echo detached-head)"
PROMPT_TEXT="$(cat "$PROMPT_FILE")"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Ralph loop (Claude Code)"
echo "Mode:   $MODE"
echo "Prompt: $PROMPT_FILE"
[[ "$EXPLAIN_MODE" != "" ]] && echo "Explain: $EXPLAIN_MODE"
[[ "$ALLOW_UNSAFE_PERMISSIONS" == "1" ]] && echo "Permissions: dangerous skip (unsafe)"
[[ "$MAX_TURNS" != "" ]] && echo "Turns:  $MAX_TURNS"
echo "Branch: $BRANCH"
[[ "$MAX_ITERATIONS" != "0" ]] && echo "Max:    $MAX_ITERATIONS"
echo "Logs:   $RUN_DIR"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

while true; do
    if [[ "$MAX_ITERATIONS" != "0" && "$ITERATION" -ge "$MAX_ITERATIONS" ]]; then
        echo "Reached max iterations: $MAX_ITERATIONS"
        break
    fi

    TS="$(date +%Y%m%d-%H%M%S)"
    JSONL_PATH="$RUN_DIR/${MODE}-${TS}.jsonl"
    FINAL_PATH="$RUN_DIR/${MODE}-${TS}.final.md"
    PRETTY_PATH="$RUN_DIR/${MODE}-${TS}.pretty.log"

    echo
    echo "==> Iteration $((ITERATION + 1))"

    CLAUDE_ARGS=(-p "$PROMPT_TEXT" --output-format stream-json)

    if [[ "$OVERLAY_PROMPT_FILE" != "" ]]; then
        if [[ ! -f "$OVERLAY_PROMPT_FILE" ]]; then
            echo "Missing overlay prompt file: $OVERLAY_PROMPT_FILE"
            exit 1
        fi
        CLAUDE_ARGS+=(--append-system-prompt-file "$OVERLAY_PROMPT_FILE")
    fi

    if [[ "$MAX_TURNS" != "" ]]; then
        CLAUDE_ARGS+=(--max-turns "$MAX_TURNS")
    fi

    if [[ "$ALLOW_UNSAFE_PERMISSIONS" == "1" ]]; then
        CLAUDE_ARGS+=(--dangerously-skip-permissions)
    fi

    if [[ "$OUTPUT_MODE" == "json" || ! -f "$RENDERER" ]]; then
        claude "${CLAUDE_ARGS[@]}" | tee "$JSONL_PATH"
    else
        claude "${CLAUDE_ARGS[@]}" \
            | tee "$JSONL_PATH" \
            | python3 -u "$RENDERER"

        if python3 "$RENDERER" < "$JSONL_PATH" > "$PRETTY_PATH"; then
            echo "Saved pretty log to:     $PRETTY_PATH"
        else
            echo "Warning: failed to write pretty log: $PRETTY_PATH"
        fi
    fi

    if [[ -f "$EXTRACTOR" ]]; then
        if python3 "$EXTRACTOR" < "$JSONL_PATH" > "$FINAL_PATH"; then
            if [[ -s "$FINAL_PATH" ]]; then
                echo "Saved final message to: $FINAL_PATH"
            else
                rm -f "$FINAL_PATH"
                echo "Warning: no final message extracted from stream"
            fi
        else
            echo "Warning: failed to extract final message: $FINAL_PATH"
        fi
    fi

    echo "Saved JSONL log to:     $JSONL_PATH"

    ITERATION=$((ITERATION + 1))

    if [[ "$MAX_ITERATIONS" == "0" ]]; then
        echo
        echo "Run again for another fresh-context iteration:"
        echo "  ./loop-claude.sh $MODE 1"
        break
    fi
done
