You are running the Ralph planning loop for this repository in Codex.

Your job is to refresh `IMPLEMENTATION_PLAN.md` so the next build loop can execute safely with fresh context.

## Mode
Plan only.
Do not edit application code.
Do not implement fixes.
Do not stage, commit, push, tag, or release anything.

## Read first
1. Read `AGENTS.md`.
2. Read `IMPLEMENTATION_PLAN.md`.
3. Read all relevant specs in `specs/`.
4. Read enough source in `src/backend/` and `src/frontend/` to verify actual implementation status.
5. Read `README.md` only as context; treat specs and code as more authoritative than stale top-level docs.

## Planning rules
- Verify before you conclude something is missing.
- Prefer a single ordered checklist in `IMPLEMENTATION_PLAN.md`.
- Keep completed items concise.
- Expand the next active phase into concrete, testable steps.
- Call out blockers, stale docs, risky assumptions, and hidden dependencies.
- If code and specs disagree, record the mismatch explicitly.
- If you discover new work, insert it in priority order instead of appending vague notes.
- Keep the plan actionable for a fresh Codex run with no memory beyond the repo files.

## Required output in `IMPLEMENTATION_PLAN.md`
Keep or rewrite the file into this shape:
1. Current status summary
2. Active phase
3. Ordered checklist with `[ ]` and `[x]`
4. Notes / discoveries that matter for the next loop
5. Next recommended build slice

## Focus for this repo
Use the current repo state to plan around:
- Phase 3 integration testing
- developer-experience cleanup
- documentation alignment for v2
- safe handling of legacy v1 files
- any gaps between specs, backend, frontend, and top-level docs

## Stop condition
When the plan is updated and internally consistent, stop.
