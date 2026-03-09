# IMPLEMENTATION_PLAN.md

## Current status
- NewsPerspective v2.0 backend and frontend are largely built.
- Phase 1, Phase 2, and Phase 2.5 appear complete from the current plan.
- The next meaningful work is integration testing, DX cleanup, and aligning docs with the real v2 architecture.
- Top-level docs are stale: `README.md` and `CLAUDE.md` still describe the old v1 root workflow, while the active app appears to live under `src/backend/` and `src/frontend/`.

## Active phase
Phase 3 — Integration, DX, and cleanup

## Ordered checklist

### Integration
- [ ] Step 15.1 — Start backend and frontend together and verify basic boot flow.
- [ ] Step 15.2 — Exercise `POST /api/refresh` with `X-News-Api-Key` and confirm article ingestion works.
- [ ] Step 15.3 — Verify frontend article list rendering, rewritten headline display, TLDR display, and article detail navigation.
- [ ] Step 15.4 — Verify frontend filters: Good News toggle, source filter, search, pagination, and empty states.
- [ ] Step 15.5 — Verify error handling for backend unavailable and invalid API key flows.
- [ ] Step 15.6 — Verify onboarding and settings dialog behaviour for add/change/remove key flows.
- [ ] Step 15.7 — Verify keyboard navigation and basic accessibility affordances across core interactive UI.
- [ ] Step 15.8 — Fix any defects discovered during Steps 15.1 through 15.7.

### Developer experience
- [x] Step 16.1 — Add `src/backend/requirements.txt` with the backend runtime dependencies.
- [ ] Step 16.2 — Add a root `Makefile` with `install`, `backend`, `frontend`, and `dev` targets if those commands are not already covered elsewhere.
- [ ] Step 16.3 — Rewrite `README.md` for the v2 architecture, setup flow, and user-provided NewsAPI key model.
- [ ] Step 16.4 — Replace Claude-era loop guidance with Codex-ready guidance where repo docs still depend on Claude-specific behaviour.
- [ ] Step 16.5 — Update `AGENTS.md` only if runtime commands or repo-wide operating rules change during this phase.

### Cleanup
- [ ] Step 17.1 — Inventory root-level legacy v1 files and confirm none are still imported by v2.
- [ ] Step 17.2 — Move legacy v1 files into `legacy/` only after docs and runtime validation are complete.
- [ ] Step 17.3 — Review `.gitignore` and related repo hygiene after legacy moves.
- [ ] Step 17.4 — Remove or archive stale loop/docs artifacts that would confuse future Codex runs.

## Notes and discoveries
- The current `CLAUDE.md` is useful as historical context but should not be treated as the active instruction surface for Codex.
- The current root `README.md` still references Streamlit, Azure AI Search, and legacy scripts; that should be treated as stale until rewritten.
- The current `AGENTS.md` already points at the v2 FastAPI + Next.js layout, so future loop runs should follow that view of the repo unless code inspection proves otherwise.
- Avoid moving legacy files before integration testing confirms v2 does not depend on them.
- Step 16.1 is complete: `src/backend/requirements.txt` now captures the backend runtime dependencies without any Azure SDK packages.
- Specs and active backend config were previously mismatched on AI provider naming; the v2 backend is now being aligned to standard `OPENAI_API_KEY` and `OPENAI_MODEL` settings.

## Next recommended build slice
Step 15.1 — boot backend and frontend together, confirm the local run commands still work, and record any missing dependencies or startup failures.
