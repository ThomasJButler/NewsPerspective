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

## Install Codex CLI
```bash
npm install -g @openai/codex
```

Then authenticate Codex locally and trust this project so project-scoped `.codex/config.toml` is loaded.

## Notes
- `codex exec` is the non-interactive entrypoint.
- Project config belongs in `.codex/config.toml`.
- Keep loop prompts repo-local and explicit; do not rely on implicit memory.
- For backend work, create the local Python environment at `src/backend/.venv`, then install `src/backend/requirements.txt`.
- Copy `.env.template` to `.env` for backend setup.
- Backend config uses `OPENAI_API_KEY`, `OPENAI_MODEL`, and `DATABASE_URL` from the repo-root `.env`.
- `NEWS_API_KEY` is request-scoped, not a backend env var; send it in the `X-News-Api-Key` header on `POST /api/refresh`.
