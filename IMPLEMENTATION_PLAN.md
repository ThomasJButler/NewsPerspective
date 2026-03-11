# IMPLEMENTATION_PLAN.md

## 1. Current status summary and code review
- Updated on 2026-03-11 after re-reading `AGENTS.md`, `README.md`, `specs/OVERVIEW.md`, `specs/BACKEND.md`, `specs/FRONTEND.md`, `specs/AI_PROMPTS.md`, recent local git history through `da68ec7`, and the relevant backend/frontend/tests on disk.
- No repo-local issue tracker or separate written code-review artifact was found. The findings below come from this planning pass, the recent local commit history, and the current working tree.
- Treat the working tree as authoritative for the next build loop. `git status --short` still shows uncommitted docs/spec changes, backend routing/tests, the manual-evidence helper, frontend package scripts, and untracked `src/frontend/tests/e2e/refresh-path.spec.ts`. Do not revert or re-implement those slices blindly.
- Verified current runtime alignment in code:
  - request-scoped `X-News-Api-Key` validation, validation-failure claim release, and duplicate-refresh short-circuit behavior are live in `src/backend/routers/sources.py`
  - cached browse still works from processed SQLite rows without a saved NewsAPI key
  - article list, sources, stats, and detail visibility are restricted to `processing_status="processed"`
  - one AI call per article still produces rewrite, sentiment, TLDR, and good-news output
  - the frontend home route currently exposes search, source, and good-news controls, while `category` remains API-only through `src/frontend/lib/api.ts` and the backend query param
  - the repo-managed refresh-path Playwright suite exists on disk at `src/frontend/tests/e2e/refresh-path.spec.ts`
  - the trusted-machine helper emits URL-aware reuse-path commands, a frontend reachability preflight, and a manual follow-up checklist
- [P1] No new repo-local correctness regression was confirmed in this pass. The remaining highest-priority gap is still external evidence: the trusted-machine Phase 3 refresh pass has not been completed with a real `NEWS_API_KEY` and a real browser outside the Codex sandbox.
- [P2] `specs/BACKEND.md` is stale. Its `Known evidence gap` note still says retry and later-category refresh-failure behavior are only lightly covered, but `src/backend/tests/test_refresh_processing.py` now covers 429 retry exhaustion, transport retry exhaustion, later-category failure after earlier success, and fail-fast-before-insert behavior.
- [P2] `src/frontend/README.md` is still partially stale. Its Playwright section matches the current harness, but the opening summary still says coverage is only for the cached-browse flow even though the maintained suite now includes `refresh-path.spec.ts`.
- [P3] `src/backend/services/refresh_tracker.py` remains in-memory and per-process. That still matches the current spec and is a documented limitation, not the next implementation target.
- Fresh validation on 2026-03-11:
  - `source src/backend/.venv/bin/activate && python3 -m unittest src.backend.tests.test_api_smoke -v` passed
  - `source src/backend/.venv/bin/activate && python3 -m unittest src.backend.tests.test_refresh_processing -v` passed
  - `source src/backend/.venv/bin/activate && python3 -m unittest src.backend.tests.test_manual_integration_evidence -v` passed
  - `cd src/frontend && npm run typecheck` passed
  - `cd src/frontend && npm run test:e2e:reuse -- --list` passed and listed 9 Playwright tests across `cached-browse.spec.ts` and `refresh-path.spec.ts`
- Browser execution was not re-run during this planning pass. The trusted-machine blocker still stands: no real `NEWS_API_KEY` and no real browser evidence are available from this Codex environment.

## 2. Active phase
Phase 3D remains active. The next product proof is the trusted-machine refresh evidence pass, but that slice can only be executed on a real local machine with a real `NEWS_API_KEY` and browser access. Inside Codex, the next safe build work is limited to doc/spec alignment for behavior that is already implemented and covered by tests. Do not recreate removed root-level v1 runtime files during this phase.

## 3. Ordered checklist with [ ] and [x]
- [x] 18.1 Enforce processed-only article detail visibility and cover `pending`/`failed` detail `404` behavior.
- [x] 18.2 Add deterministic Playwright coverage for accepted refresh, invalid-key UX, duplicate-refresh attach behavior, polling, and timeout handling.
- [x] 18.3 Expose safe Playwright entrypoints for repo-managed ports versus reuse of an already running local stack.
- [x] 18.4 Align top-level docs/specs with the v2 runtime and the 2026-03-10 removal of root-level v1 runtime files.
- [x] 18.5 Align the documented frontend filter surface with the shipped home page, which exposes search, source, and good-news controls while `category` remains API-only.
- [x] 18.6 Add backend regression coverage for fetch retry exhaustion, later-category failure, fail-fast-before-insert behavior, and refresh-claim state handling.
- [x] 18.7a Make the trusted-machine Phase 3 evidence flow explicit across `README.md`, `src/frontend/README.md`, and `src/backend/scripts/capture_manual_integration_evidence.py`.
- [x] 18.7b Improve the trusted-machine helper report with URL-aware commands, frontend reachability preflight, a manual checklist, and paste-ready follow-up notes.
- [ ] 18.7 Finish the trusted-machine Phase 3 evidence pass on a real local machine:
  Run `source src/backend/.venv/bin/activate && python -m src.backend.scripts.seed_manual_integration_data` first if cached browse needs seed data.
  Run `python -m src.backend.scripts.capture_manual_integration_evidence --api-key "$NEWS_API_KEY" --output /tmp/phase3-manual-integration.md` against the already running local stack.
  Keep that backend/frontend stack running and execute the exact reuse-path Playwright command printed in the generated report.
  Open the frontend URL from the report, complete the frontend follow-up table with exact cached-browse and refresh UI outcomes, and paste the final observed results back into this file.
- [ ] 18.8 Remove stale backend-spec drift. Update `specs/BACKEND.md` so the `Known evidence gap` wording matches the now-landed coverage in `src/backend/tests/test_refresh_processing.py`.
- [ ] 18.9 Remove the remaining frontend README drift. Update the opening summary in `src/frontend/README.md` so it no longer implies Playwright only covers cached browse.
- [ ] 18.10 After 18.8 or 18.9, run the smallest proof set for the edited doc slice:
  use targeted `rg` checks to confirm the stale wording is gone
  if `specs/BACKEND.md` changes, re-run `source src/backend/.venv/bin/activate && python3 -m unittest src.backend.tests.test_refresh_processing -v`
  if `src/frontend/README.md` changes, re-run `cd src/frontend && npm run test:e2e:reuse -- --list`

## 4. Notes / discoveries that matter for the next loop
- The workspace is ahead of committed history. `HEAD` is `da68ec7`, but the working tree includes uncommitted changes in `AGENTS.md`, `README.md`, `READMEOLD.md`, `specs/BACKEND.md`, `specs/FRONTEND.md`, `specs/OVERVIEW.md`, `src/backend/routers/articles.py`, `src/backend/scripts/capture_manual_integration_evidence.py`, `src/backend/tests/test_api_smoke.py`, `src/backend/tests/test_manual_integration_evidence.py`, `src/frontend/README.md`, `src/frontend/package.json`, and untracked `src/frontend/tests/e2e/refresh-path.spec.ts`. Build against the files on disk.
- `specs/BACKEND.md` already reflects the processed-only detail-route policy in the working tree. The remaining stale part is specifically the retry and later-category failure coverage note near the refresh pipeline section.
- `src/frontend/README.md` already documents `npm run test:e2e`, `npm run test:e2e:reuse`, and the trusted-machine helper pairing. The remaining mismatch is the opening summary at the top of the file, not the Playwright section itself.
- `src/frontend/playwright.config.mts` still assumes ownership of `127.0.0.1:8000` and `127.0.0.1:3000` unless `PLAYWRIGHT_SKIP_WEBSERVER=1` is set. Use `npm run test:e2e` only when those ports are free; otherwise use `npm run test:e2e:reuse`.
- The repo-managed refresh-path Playwright suite is intentionally browser-mocked. It validates frontend UX contracts, but it does not replace the real-key trusted-machine evidence pass.
- `src/frontend/lib/api.ts` and `src/backend/routers/articles.py` still support a `category` query param even though `src/frontend/app/page.tsx` does not render a category control. That is current behavior, not a regression.
- `README.md`, `specs/OVERVIEW.md`, and `specs/FRONTEND.md` are aligned with the current tree for the slices checked here. The only concrete stale-doc gaps confirmed in this review are `specs/BACKEND.md` and the opening summary in `src/frontend/README.md`.
- Legacy v1 runtime files remain absent from the repo root. Use git history or `READMEOLD.md` for legacy reference, and do not recreate root-level v1 runtime files during v2 work.
- This sandbox still cannot be relied on for `.git` writes. If a later build slice needs a commit, stage and commit outside this restricted Codex environment.

## 5. Next recommended build slice
- If the next build loop is still running inside Codex, take 18.8 next. It is the highest-priority unchecked item that is fully executable here and removes the clearest confirmed spec mismatch.
- After 18.8, take 18.9 next. It is a small documentation cleanup and the only remaining repo-local frontend doc drift confirmed in this pass.
- If the next build loop is on a trusted local machine with a real `NEWS_API_KEY` and browser access, take 18.7 instead and paste the exact observed results back into this file before returning to doc cleanup.
