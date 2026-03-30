# IMPLEMENTATION_PLAN.md

## 1. Current status summary

Updated on 2026-03-30 (project audit and cleanup pass, Claude Code; frontend production build revalidated in Ralph build loop).

### Project scope

NewsPerspective v3.0 is a **self-hosted personal news reader**. It runs locally with user-supplied API keys (OpenAI + NewsAPI free tier). It is not a live deployment or hosted service — the NewsAPI free tier restricts requests to localhost.

### Verified implementation state

- Backend (`src/backend/`): FastAPI + SQLite, version `3.0.0`. All core features shipped: cached browse, refresh with `X-News-Api-Key` header, single AI call per article (sentiment, rewrite, TLDR, good-news flag), content guardrails, article comparison, good news filtering (excludes sports, entertainment, politics).
- Frontend (`src/frontend/`): Next.js 16 + React 19 + ShadCN UI, version `3.0.0`. All core features shipped: article feed with filters, search, settings dialog, API key management, refresh status polling, comparison view, about modal, dark mode.
- Backend tests: 61 test methods across 6 test modules. P1 test isolation fix (AIService `__init__` mock) was already applied.
- Frontend static checks: lint, typecheck, and production build pass (2026-03-30). 7 helper tests pass. Playwright e2e tests exist for cached-browse and refresh-path flows.
- Specs: `specs/OVERVIEW.md`, `specs/BACKEND.md`, `specs/FRONTEND.md` are current. `specs/ROADMAP.md` updated to remove speculative monetisation language.

### Cleanup completed this pass

- Deleted `twinkly-yawning-minsky.md` (superseded scratch planning doc)
- Deleted `READMEOLD.md` (legacy v1 stub — git history is sufficient)
- Deleted `RALPH_CODEX_MIGRATION_NOTES.md` (one-time migration guide, no longer needed)
- Deleted `next-steps.txt` (QA checklist folded into this plan below)
- Updated `README.md` to frame the project as self-hosted/personal, removed CLA language, clarified localhost-only NewsAPI restriction
- Updated `specs/ROADMAP.md` to remove speculative monetisation direction

## 2. Active phase

**Finishing up.** The project is functionally complete. Remaining work is local validation and manual QA before considering the v3.0 MVP done.

## 3. Ordered checklist

- [x] Project audit: read all docs, specs, source, and test state
- [x] Delete scratch/historical files (twinkly-yawning-minsky.md, READMEOLD.md, RALPH_CODEX_MIGRATION_NOTES.md, next-steps.txt)
- [x] Verify P1 test isolation fix is already applied (confirmed: `__init__` mock present in both tests)
- [x] Update README.md for personal/local project framing
- [x] Update specs/ROADMAP.md to remove stale monetisation and loop order sections
- [x] Rewrite IMPLEMENTATION_PLAN.md with fresh audit results
- [x] Run full backend test suite and confirm all pass (113/113 passed, 2026-03-30)
- [x] Run frontend lint + typecheck and confirm all pass (2026-03-30)
- [x] Run `cd src/frontend && npm run build` and confirm production build succeeds (passed, 2026-03-30)
- [ ] Manual QA: fresh database, no saved key (see checklist below)
- [ ] Manual QA: refresh with valid and invalid keys
- [ ] Manual QA: guardrails, good news filter, comparison view
- [ ] Manual QA: settings dialog key management
- [ ] Manual QA: refresh status persistence across restart

## 4. Manual QA checklist

Run through these with the app running locally (`uvicorn` on 8000, `npm run dev` on 3000).

1. **Fresh database, no saved key** — app loads, inline onboarding card visible, empty-state copy shown
2. **Refresh blocked without key** — clicking refresh without a saved key shows guidance, does not start backend refresh
3. **Seeded data path** — `python -m src.backend.scripts.seed_manual_integration_data` populates articles; they appear without needing a key
4. **Valid NewsAPI key** — save key in inline form or settings, trigger refresh, see processing state, see terminal success, feed/stats update
5. **Invalid NewsAPI key** — use fake key, trigger refresh, see clean error state, no fake success
6. **Duplicate refresh** — start refresh, trigger again mid-flight, UI attaches to existing refresh instead of showing dual success
7. **Settings key management** — add, update, remove key; cached browsing still works after removal; onboarding card returns
8. **Guardrails** — add blocked topic in settings, matching stories disappear, remove topic, stories return
9. **Good News filter** — enable, confirm sports/entertainment/politics excluded
10. **Comparison view** — open `/comparison`, confirm grouping and AI analysis renders
11. **Refresh status persistence** — complete refresh, restart backend, reload frontend, confirm no broken in-progress state
12. **Production build** — `cd src/frontend && npm run build` completes successfully

## 5. Notes

- The Ralph loop files (`AGENTS.md`, `PROMPT_*.md`, `loop*.sh`) remain at root for future iteration use.
- The `logs/` directory contains historical runtime logs and the `phase3_manual_integration_report.md` — these are fine to keep as historical artifacts.
- The `specs/completedarchive/` directory has two dated archive files from prior implementation passes.
- The `.env.template` correctly documents that `NEWS_API_KEY` is not a backend env var.
- Docker workflow (`src/frontend/compose.yaml`, `Dockerfile`) exists for quick local testing and Playwright e2e.

## 6. Next recommended action

Start the manual QA checklist with a fresh database and no saved key, then continue through refresh, guardrails, comparison, settings, and restart-persistence checks. If those pass, the v3.0 MVP is done.
