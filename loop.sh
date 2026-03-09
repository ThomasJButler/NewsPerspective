#!/usr/bin/env bash
set -euo pipefail

# Ralph loop wrapper for Codex
# Usage:
#   ./loop.sh plan
#   ./loop.sh plan 1
#   ./loop.sh build
#   ./loop.sh build 2

MODE="${1:-build}"
MAX_ITERATIONS="${2:-0}"

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
      echo "Usage: ./loop.sh [plan|build] [max_iterations]"
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

ITERATION=0
BRANCH="$(git branch --show-current 2>/dev/null || echo detached-head)"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Ralph loop (Codex)"
echo "Mode:   $MODE"
echo "Prompt: $PROMPT_FILE"
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

  echo
  echo "==> Iteration $((ITERATION + 1))"

  codex exec --full-auto --json \
    --output-last-message "$FINAL_PATH" \
    "$(cat "$PROMPT_FILE")" \
    | tee "$JSONL_PATH"

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
