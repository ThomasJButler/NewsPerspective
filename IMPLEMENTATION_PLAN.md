# IMPLEMENTATION_PLAN.md

## Current status summary
- Re-verified on 2026-03-09 that the active v2 runtime is `src/backend/` plus `src/frontend/`; `src/` does not import the root-level legacy v1 Python files.
- Re-ran the backend smoke baseline with `fastapi.testclient.TestClient`: `GET /api/articles`, `GET /api/sources`, and `GET /api/stats` return `200`; `GET /api/articles/not-a-real-id` returns `404`; `POST /api/refresh` returns `401` when `X-News-Api-Key` is missing.
- Resolved the backend dependency-install contract on 2026-03-09 by adding `src/backend/requirements.txt` as a thin wrapper around the root `requirements.txt`; the documented install command `source src/backend/.venv/bin/activate && python -m pip install -r src/backend/requirements.txt` now succeeds.
- Resolved the v2 environment-file contract on 2026-03-09 by adding a root `.env.template` for `OPENAI_API_KEY`, `OPENAI_MODEL`, and `DATABASE_URL`, documenting that `NEWS_API_KEY` is request-scoped via `X-News-Api-Key`, and removing the stale `.gitignore` rule that would have hidden the template from the repo.
- Resolved the Step 15.3 repo-hygiene slice on 2026-03-09 by ignoring `.codex-run/`, removing the stale `.gitignore` entry for the tracked runtime file `src/backend/config.py`, and setting `turbopack.root` in `src/frontend/next.config.ts` to pin the frontend workspace root explicitly.
- The local SQLite state is still empty (`total_articles: 0`), so success-path ingestion, populated detail views, and invalid-key versus valid-key refresh behavior still need a live integration pass with network access and a real NewsAPI key.
- Re-ran the frontend build during Step 15.3: the prior Next.js workspace-root inference warning no longer appears after setting `turbopack.root`, but `npm run build` still fails under the sandbox with the same Turbopack panic (`Failed to write app endpoint /page` caused by `creating new process` -> `binding to a port` -> `Operation not permitted`).
- Phase 3 integration remains gated by setup/docs drift, the frontend no-key browse regression, the source-filter contract mismatch, stale v2 docs, unresolved legacy-file handling, and the lack of automated tests.

## Active phase
Phase 3A - integration preflight, developer-experience cleanup, v2 documentation alignment, and legacy-boundary prep

## Ordered checklist
- [x] Step 14.1 - Verify the active v2 runtime lives in `src/backend/` and `src/frontend/`.
- [x] Step 14.2 - Verify the v2 code in `src/` does not import the root-level legacy v1 runtime files.
- [x] Step 14.3 - Smoke-test the backend read-only API locally with `TestClient`.
- [x] Step 14.4 - Capture the frontend validation baseline with `npm run lint` and `npm run build`.
- [x] Step 15.1 - Resolve the backend dependency-install contract for a fresh clone: either add `src/backend/requirements.txt` that matches the actual runtime dependencies or realign every v2 doc/loop instruction to the root `requirements.txt`, then verify the documented backend install command references a file that exists.
- [x] Step 15.2 - Resolve the v2 environment-file contract: either add a root `.env.template` that documents `OPENAI_API_KEY`, `OPENAI_MODEL`, and `DATABASE_URL`, or stop implying that template/file exists; make sure docs state that `NEWS_API_KEY` is request-scoped via `X-News-Api-Key`, not a backend env var.
- [x] Step 15.3 - Clean repo hygiene for repeatable Ralph runs: ignore `.codex-run/`, remove or document stale `.gitignore` entries such as `src/backend/config.py` that hide real runtime files from repo discovery, and decide whether `src/frontend/next.config.ts` should set an explicit `turbopack.root` to silence workspace-root inference noise.
- [ ] Step 15.4 - Fix the frontend lint blockers in `src/frontend/components/theme-toggle.tsx` and `src/frontend/hooks/use-api-key.ts`, then re-run `npm run lint` and either fix or explicitly defer the remaining `no-img-element` warning in `src/frontend/app/article/[id]/page.tsx`.
- [ ] Step 15.5 - Fix the no-key browsing flow so cached articles, sources, and stats remain visible without a stored NewsAPI key, while refresh still requires `X-News-Api-Key`; keep a visible path to add/update/remove the key and make the refresh button behavior explicit when no key is stored.
- [ ] Step 15.6 - Fix the source-filter contract end-to-end: the frontend currently sends `source_id`, the backend filters by `source_name`, and NewsAPI records with missing `source.id` values normalize to `""`, which makes current Select values and React keys unstable.
- [ ] Step 15.7 - Re-run local validation after Steps 15.1-15.6: backend smoke tests, `npm run lint`, and `npm run build`; if Next.js build still fails only in the sandbox, capture the exact remaining blocker and whether it reproduces outside the sandbox.
- [ ] Step 15.8 - Run manual API integration checks against a live backend for `/api/articles`, `/api/articles/{id}`, `/api/sources`, `/api/stats`, and `/api/refresh` with missing, invalid, and valid `X-News-Api-Key` values.
- [ ] Step 15.9 - Re-test the core frontend flow against the local backend: cached feed load without a key, API-key onboarding, refresh messaging, rewritten headline display, TLDR display, detail navigation, search, source filter, good-news toggle, pagination, and empty states.
- [ ] Step 15.10 - Verify degraded states and accessibility: backend unavailable, empty database, invalid-key messaging, slow background refresh completion, keyboard navigation, and icon-button labeling.
- [ ] Step 16.1 - Rewrite the root `README.md` so it documents the actual v2 app architecture, backend/frontend setup, env vars, refresh flow, validation commands, and the legacy-file boundary instead of only the Ralph loop.
- [ ] Step 16.2 - Replace or trim stale sub-docs that conflict with v2, starting with `src/frontend/README.md`; keep `READMEOLD.md` explicitly legacy-only.
- [ ] Step 16.3 - Reconcile remaining spec/doc drift explicitly after the code path is settled: Azure OpenAI wording in `specs/OVERVIEW.md`, Next.js 15 vs 16.1.6, `/v2/top-headlines` plus `/v2/everything` vs the current categorized `top-headlines` fetcher, and `specs/OVERVIEW.md` wording that implies only `NEWS_API_KEY` is required.
- [ ] Step 16.4 - Add a small root `Makefile` only if setup is still error-prone after Steps 15.1-16.3.
- [ ] Step 17.1 - Inventory the root-level legacy v1 files and decide which stay in place as reference versus move into a dedicated `legacy/` directory.
- [ ] Step 17.2 - Move or archive legacy v1 files only after the integration checklist and doc rewrite are complete.
- [ ] Step 17.3 - Revisit `.gitignore` after any legacy move so ignored tracked files, loop artifacts, and v2 setup files are not masking required repo state.

## Notes / discoveries that matter for the next loop
- `src/backend/requirements.txt` now exists and delegates to the root `requirements.txt`, so the repo keeps a single backend dependency source of truth while preserving the documented `pip install -r src/backend/requirements.txt` workflow.
- The repo now ships a root `.env.template` with `OPENAI_API_KEY`, `OPENAI_MODEL`, and `DATABASE_URL`, and the root `README.md` now tells developers to copy it to `.env`.
- `.gitignore` now ignores `.codex-run/`, so repeated Ralph runs should stop surfacing loop output as untracked repo noise.
- The stale `.gitignore` entry for `src/backend/config.py` is gone, and `rg --files` from the repo root now includes that tracked runtime file again.
- The backend already satisfies the product rule that read-only endpoints work without a NewsAPI key. The frontend still violates that rule because `src/frontend/app/page.tsx` returns `ApiKeySetup` whenever no key is stored.
- The no-key browse fix has a hidden dependency: once the full-page onboarding gate is removed, the app still needs a discoverable way to add/update/remove the key and a defined refresh UX. Right now `Header` and `SettingsDialog` are only reachable inside the gated view, and `handleRefresh()` silently returns when `apiKey` is empty.
- The source-filter issue is broader than a query-param mismatch: `news_fetcher._normalize()` converts missing NewsAPI `source.id` values to `""`, while `src/frontend/components/source-filter.tsx` uses `source_id` for both the Select value and the React key. Multiple sources can therefore collapse onto the same empty identifier even before the backend filter mismatch is fixed.
- `npm run lint` currently fails with two errors and one warning:
  - `src/frontend/components/theme-toggle.tsx`: `react-hooks/set-state-in-effect`
  - `src/frontend/hooks/use-api-key.ts`: `react-hooks/set-state-in-effect`
  - `src/frontend/app/article/[id]/page.tsx`: `@next/next/no-img-element` warning
- `npm run build` is still not a reliable repo validation in this sandbox:
  - The prior Next.js workspace-root inference warning is resolved by the explicit `turbopack.root` in `src/frontend/next.config.ts`
  - Turbopack then panics with `Failed to write app endpoint /page`, caused by `creating new process` -> `binding to a port` -> `Operation not permitted`, which still looks sandbox-specific until reproduced elsewhere
- The current local database contains no processed articles, so successful detail-view integration and refresh-driven ingestion were not verifiable here without external network access and a real NewsAPI key.
- `POST /api/refresh` correctly rejects a missing `X-News-Api-Key` with `401`. Invalid-key versus valid-key behavior still needs confirmation in a network-enabled environment.
- There are still no automated tests under `src/`; current validation is smoke-test plus manual checks only.
- `src/frontend/README.md` is still default `create-next-app` boilerplate and should not be treated as project documentation.
- Additional explicit spec/code drift still needs resolution:
  - `specs/OVERVIEW.md` still shows Azure OpenAI in the architecture diagram, while the backend uses the standard OpenAI client with `OPENAI_API_KEY`
  - `specs/BACKEND.md` says the fetcher uses both `/v2/top-headlines` and `/v2/everything`; `src/backend/services/news_fetcher.py` currently uses categorized `/v2/top-headlines` only
  - `specs/FRONTEND.md` says Next.js 15, while `src/frontend/package.json` is on Next.js 16.1.6
  - `specs/OVERVIEW.md` says NewsAPI "only requires `NEWS_API_KEY`", which is incomplete for the deployed system because backend AI processing still depends on `OPENAI_API_KEY` unless neutral fallbacks are acceptable
- Root-level legacy Python files still present at repo root: `azure_ai_language.py`, `azure_document_intelligence.py`, `batch_processor.py`, `logger_config.py`, `run.py`, `search.py`, and `web_app.py`.

## Next recommended build slice
Step 15.4 - fix the frontend lint blockers in `src/frontend/components/theme-toggle.tsx` and `src/frontend/hooks/use-api-key.ts`, then re-run `npm run lint` and either fix or explicitly defer the remaining `@next/next/no-img-element` warning in `src/frontend/app/article/[id]/page.tsx`.
