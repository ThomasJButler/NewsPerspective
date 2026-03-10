#!/usr/bin/env bash
set -euo pipefail

# Ralph loop wrapper for Codex
# Usage:
#   ./loop.sh plan
#   ./loop.sh plan 1
#   ./loop.sh build
#   ./loop.sh build 2
#   ./loop.sh build coach
#   ./loop.sh build 1 coach
#   ./loop.sh build homer
#   ./loop.sh build 1 homer
#
# Common runs:
#   ./loop.sh plan 1
#     Pretty output, normal narration, one planning iteration
#   ./loop.sh plan 1 coach
#     Pretty output, coach narration, one planning iteration
#   ./loop.sh plan 1 homer
#     Pretty output, simple foundations narration, one planning iteration
#   ./loop.sh build 1
#     Pretty output, normal narration, one build iteration
#   ./loop.sh build 1 coach
#     Pretty output, coach narration, one build iteration
#   ./loop.sh build 1 homer
#     Pretty output, simple foundations narration, one build iteration
#   RALPH_OUTPUT_MODE=json ./loop.sh build 1
#     Raw JSON terminal output instead of pretty rendering
#   RALPH_OUTPUT_MODE=json ./loop.sh plan 1
#     Raw JSON terminal output for planning runs
#   RALPH_ALLOW_UNSAFE_SANDBOX=1 ./loop.sh build 1
#     Trusted-local full-access run so the loop can write to `.git` and commit
#   RALPH_ALLOW_UNSAFE_SANDBOX=1 ./loop.sh build 1 coach
#     Trusted-local full-access run with coach narration
#   RALPH_ALLOW_UNSAFE_SANDBOX=1 ./loop.sh build 1 homer
#     Trusted-local full-access run with simple foundations narration
#   RALPH_ALLOW_UNSAFE_SANDBOX=1 ./loop.sh build 1 (ONLY WHEN NEED TO COMMIT)

MODE="${1:-build}"
MAX_ITERATIONS="${2:-0}"
EXPLAIN_MODE="${RALPH_EXPLAIN_MODE:-}"
ALLOW_UNSAFE_SANDBOX="${RALPH_ALLOW_UNSAFE_SANDBOX:-0}"

if [[ "${RALPH_COACH_MODE:-0}" == "1" ]]; then
  EXPLAIN_MODE="coach"
fi

if [[ "${RALPH_HOMER_MODE:-0}" == "1" ]]; then
  EXPLAIN_MODE="homer"
fi

if [[ "${2:-}" == "coach" || "${2:-}" == "homer" ]]; then
  MAX_ITERATIONS="0"
  EXPLAIN_MODE="${2:-}"
fi

if [[ "${3:-}" == "coach" || "${3:-}" == "homer" ]]; then
  EXPLAIN_MODE="${3:-}"
fi

if [[ "$EXPLAIN_MODE" != "" && "$EXPLAIN_MODE" != "coach" && "$EXPLAIN_MODE" != "homer" ]]; then
  echo "Unsupported explain mode: $EXPLAIN_MODE"
  exit 1
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
      echo "Usage: ./loop.sh [plan|build] [max_iterations] [coach|homer]"
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

RUN_DIR=".codex-run"
mkdir -p "$RUN_DIR"
RENDERER="scripts/render_codex_exec_stream.py"
OUTPUT_MODE="${RALPH_OUTPUT_MODE:-pretty}"
OVERLAY_PROMPT_FILE=""

ITERATION=0
BRANCH="$(git branch --show-current 2>/dev/null || echo detached-head)"
PROMPT_TEXT="$(cat "$PROMPT_FILE")"

if [[ "$EXPLAIN_MODE" == "coach" ]]; then
  OVERLAY_PROMPT_FILE="PROMPT_coach.md"
elif [[ "$EXPLAIN_MODE" == "homer" ]]; then
  OVERLAY_PROMPT_FILE="PROMPT_homer.md"
fi

if [[ "$OVERLAY_PROMPT_FILE" != "" ]]; then
  if [[ ! -f "$OVERLAY_PROMPT_FILE" ]]; then
    echo "Missing overlay prompt file: $OVERLAY_PROMPT_FILE"
    exit 1
  fi
  PROMPT_TEXT="${PROMPT_TEXT}"$'\n\n'"$(cat "$OVERLAY_PROMPT_FILE")"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Ralph loop (Codex)"
echo "Mode:   $MODE"
echo "Prompt: $PROMPT_FILE"
[[ "$EXPLAIN_MODE" != "" ]] && echo "Explain: $EXPLAIN_MODE"
[[ "$ALLOW_UNSAFE_SANDBOX" == "1" ]] && echo "Sandbox: full-access (unsafe)"
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

  EXEC_ARGS=(exec --json --output-last-message "$FINAL_PATH" -)
  if [[ "$ALLOW_UNSAFE_SANDBOX" == "1" ]]; then
    EXEC_ARGS+=(--dangerously-bypass-approvals-and-sandbox)
  else
    EXEC_ARGS+=(--full-auto)
  fi

  if [[ "$OUTPUT_MODE" == "json" || ! -f "$RENDERER" ]]; then
    printf '%s\n' "$PROMPT_TEXT" \
      | codex "${EXEC_ARGS[@]}" \
      | tee "$JSONL_PATH"
  else
    printf '%s\n' "$PROMPT_TEXT" \
      | codex "${EXEC_ARGS[@]}" \
      | tee "$JSONL_PATH" \
      | python3 -u "$RENDERER"

    if python3 "$RENDERER" < "$JSONL_PATH" > "$PRETTY_PATH"; then
      echo "Saved pretty log to:     $PRETTY_PATH"
    else
      echo "Warning: failed to write pretty log: $PRETTY_PATH"
    fi
  fi

  echo "Saved final message to: $FINAL_PATH"
  echo "Saved JSONL log to:     $JSONL_PATH"

  ITERATION=$((ITERATION + 1))

  if [[ "$MAX_ITERATIONS" == "0" ]]; then
    echo
    echo "Run again for another fresh-context iteration:"
    echo "  ./loop.sh $MODE 1"
    break
  fi
done
