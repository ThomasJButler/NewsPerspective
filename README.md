# NewsPerspective — Ralph loop for Codex

This repo is being operated with a Codex-ready Ralph Wiggum loop.

## Ralph files
- `AGENTS.md` — stable repo operating rules
- `PROMPT_plan.md` — planning loop prompt
- `PROMPT_build.md` — build loop prompt
- `IMPLEMENTATION_PLAN.md` — persistent execution state
- `loop.sh` — convenience wrapper around `codex exec`

## What changed from the old Claude loop
- Prompts are rewritten for Codex, not Claude.
- The loop uses `codex exec` for non-interactive runs.
- Automatic push and tagging have been removed.
- `AGENTS.md` is the active instruction surface for Codex.
- `CLAUDE.md` may remain in the repo as historical context, but it should not drive the Codex loop.

## Suggested repo workflow
1. Run a planning pass when the plan is stale:
   ```bash
   ./loop.sh plan 1
   ```
2. Review `IMPLEMENTATION_PLAN.md`.
3. Run one build slice:
   ```bash
   ./loop.sh build 1
   ```
4. Repeat with fresh context.

Build runs should now commit each completed, validated slice as they go. Planning runs should still commit only planning/doc changes when you explicitly want those persisted.

## Loop output
- `./loop.sh` now shows a readable live stream by default: agent messages, command starts, command pass/fail, and condensed failure excerpts.
- Raw Codex event logs are still written unchanged to `.codex-run/*.jsonl`.
- A rendered plain-text companion log is also written as `.codex-run/*.pretty.log` in pretty mode.
- The last assistant response is still written to `.codex-run/*.final.md`.
- To force the old raw JSONL terminal stream, run `RALPH_OUTPUT_MODE=json ./loop.sh build 1` or `RALPH_OUTPUT_MODE=json ./loop.sh plan 1`.

## Explain modes
- `coach` mode explains the reasoning trail in a senior-engineer style: what it is checking, what it learned, what it validated, and what comes next.
- `homer` mode explains the same work in simpler language, with short foundation-level `Simple` blocks for tired or learning-first runs.
- Build mode benefits most from these, but the same toggles also work for planning runs.
- Examples:
  ```bash
  ./loop.sh build coach
  ./loop.sh build 1 coach
  ./loop.sh build homer
  ./loop.sh build 1 homer
  ./loop.sh plan 1 coach
  ./loop.sh plan 1 homer
  RALPH_COACH_MODE=1 ./loop.sh build 1
  RALPH_HOMER_MODE=1 ./loop.sh build 1
  RALPH_EXPLAIN_MODE=homer ./loop.sh build 1
  ```

## Sandbox and git commits
- The default loop runs in Codex's normal sandboxed automatic mode.
- In some environments, that sandbox allows worktree edits but blocks writes inside `.git`, which prevents staging and committing from inside the loop.
- If you are on a trusted local machine and want the loop to be able to write to `.git`, you can opt in to full access:
  ```bash
  RALPH_ALLOW_UNSAFE_SANDBOX=1 ./loop.sh build 1
  ```
- This uses Codex's dangerous full-access mode. It is intentionally not the default.

## Install Codex CLI
```bash
npm install -g @openai/codex
```

Then authenticate Codex locally and trust this project so project-scoped `.codex/config.toml` is loaded.

## Notes
- `codex exec` is the non-interactive entrypoint.
- Project config belongs in `.codex/config.toml`.
- Keep loop prompts repo-local and explicit; do not rely on implicit memory.
- Build-mode commits are intended to be small, scoped, and validation-backed. Incomplete or failing slices should update the plan and stop without committing.
- If build-mode commits fail with `.git/index.lock` permission errors, the likely cause is the sandbox blocking `.git` writes. Use `RALPH_ALLOW_UNSAFE_SANDBOX=1` only on a trusted local machine if you want the loop to stage/commit directly.
- Frontend validation is currently pinned to Node `22.17.0` via the repo-root `.nvmrc`; in `src/frontend`, run `npm run lint`, `npm run typecheck`, and `npm run build`.
- For backend work, create the local Python environment at `src/backend/.venv`, then install `src/backend/requirements.txt`.
- Copy `.env.template` to `.env` for backend setup.
- Backend config uses `OPENAI_API_KEY`, `OPENAI_MODEL`, and `DATABASE_URL` from the repo-root `.env`.
- `NEWS_API_KEY` is request-scoped, not a backend env var; send it in the `X-News-Api-Key` header on `POST /api/refresh`.
