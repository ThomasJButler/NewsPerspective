# IMPLEMENTATION_PLAN.md

## Current status summary and code review
- Re-checked on 2026-03-10 in plan mode. Read `AGENTS.md`, `IMPLEMENTATION_PLAN.md`, `README.md`, `READMEOLD.md`, all files in `specs/`, recent git history, current worktree diffs, and the backend/frontend files that define the live v2 contract.
- Searched the repo for repo-local issue tracker entries and written code-review notes. None were found. The findings below are the current planning/code-review notes from this verification pass.
- Recent landed slices in git history confirm the current direction: frontend DX guardrails (`49274c6`), seeded Playwright cached-browse coverage (`efa45d2`), manual integration evidence helper (`0c65e40`), source normalization (`0b8a268`), and the US NewsAPI default (`cc8a629`).
- Verified live backend contract from source:
  - `src/backend/main.py` is the active FastAPI app and mounts only the v2 routers under `src/backend/`.
  - `POST /api/refresh` requires `X-News-Api-Key`, validates that key against NewsAPI `GET /v2/top-headlines` with `country=us`, `pageSize=1`, and a 5-second timeout, then starts background processing.
  - `POST /api/refresh` returns typed error codes for missing key, invalid key, upstream timeout, and upstream transport failure.
  - Duplicate refresh requests short-circuit before NewsAPI validation and return `{ "status": "processing", "message": "Refresh already in progress." }`.
  - `GET /api/refresh/status` exists and returns the in-memory tracker state from `src/backend/services/refresh_tracker.py`.
  - `GET /api/articles`, `GET /api/sources`, and `GET /api/stats` serve processed cached rows without requiring a NewsAPI key.
  - `GET /api/articles/{id}` returns by id without filtering on `processing_status`, unlike the list/source/stats endpoints.
  - Source labels are normalized consistently across list/detail/source/stats responses by trimming blanks and falling back to `source_id`, then `"Unknown source"`.
  - `src/backend/services/news_fetcher.py` now fetches category-specific NewsAPI top headlines only; it no longer uses `/v2/everything`.
  - `src/backend/services/ai_service.py` still performs a single OpenAI chat-completions call per article and falls back to neutral defaults when AI config is unavailable or parsing fails.
- Verified live frontend contract from source:
  - `src/frontend/app/page.tsx` keeps cached browsing available without a saved key and shows the inline `ApiKeySetup` card only when no key is stored.
  - NewsAPI keys are stored in `localStorage` via `src/frontend/hooks/use-api-key.ts`; read-only endpoints do not attach that key, while refresh requests attach `X-News-Api-Key`.
  - The home page polls `/api/refresh/status` every second for up to 120 seconds after refresh starts.
  - Missing-key and invalid-key refresh responses reopen settings with targeted feedback.
  - `src/frontend/next.config.ts` is the live config file and still proxies `/api/:path*` to `http://localhost:8000/api/:path*`; local frontend integration still depends on a separate backend listener on port `8000`.
  - Repo-owned Playwright coverage exists for seeded cached browse, source filtering, search, and article detail in `src/frontend/tests/e2e/cached-browse.spec.ts`.
- Validation rerun on 2026-03-10:
  - `source src/backend/.venv/bin/activate && python -m unittest src.backend.tests.test_api_smoke -v` passed all 14 tests.
  - `source src/backend/.venv/bin/activate && python -m unittest src.backend.tests.test_manual_integration_evidence -v` passed all 5 tests.
  - `cd src/frontend && node -v` reported `v22.17.0`.
  - `cd src/frontend && npm run lint` passed.
  - `cd src/frontend && npm run typecheck` passed.
  - `cd src/frontend && npx tsc --noEmit --incremental false` passed.
  - `cd src/frontend && npx playwright test tests/e2e/cached-browse.spec.ts` passed both seeded cached-browse tests.
  - `cd src/frontend && npm run build` still failed in this Codex sandbox because Turbopack panicked while creating a CSS worker process and binding to a port (`Operation not permitted`).
  - `cd src/frontend && npx next build --webpack` passed.
- Current code review findings, highest risk first:
  - [P1] Background refresh can report a false success. `src/backend/services/news_fetcher.py` returns `[]` for upstream failures and non-`ok` NewsAPI payloads, `src/backend/services/article_processor.py` treats that as a normal empty run, and `process_new_articles_background()` then marks the refresh `completed`. A transient NewsAPI outage, rate limit, or post-validation quota failure can therefore surface as "Refresh complete" with no new articles instead of a failed refresh.
  - [P1] Trusted-machine Phase 3 manual integration evidence is still missing. The helper, backend smoke coverage, and seeded browser coverage exist, but there is still no recorded local run with a real NewsAPI key and real local servers.
  - [P1] Top-level docs and specs still drift materially from the running v2 app:
    - `README.md` is still Ralph-loop-first instead of app-first.
    - `src/frontend/README.md` is still stock Next.js boilerplate.
    - `READMEOLD.md` still contains live v2 setup guidance even though it is labeled legacy.
    - `specs/OVERVIEW.md` still describes Azure-era architecture and stale NewsAPI assumptions.
    - `specs/BACKEND.md` still describes UK-focused `/v2/everything` behavior and omits `/api/refresh/status`, duplicate-refresh behavior, typed refresh errors, the 5-second validation timeout, and current source normalization behavior.
    - `specs/FRONTEND.md` still describes fullscreen first-visit onboarding, `next.config.js`, and other older assumptions instead of the current inline cached-browse-first UX on Next.js `16.1.6`.
  - [P2] The frontend duplicate-refresh path can falsely tell the user that their saved key was accepted. The backend intentionally short-circuits duplicate refresh requests before validating the key, but `src/frontend/app/page.tsx` ignores the `"Refresh already in progress."` response body and later shows accepted-key feedback after the other refresh finishes.
  - [P2] Browser back/forward navigation can desynchronise the URL from the frontend filter/search state. `src/frontend/app/page.tsx` seeds `searchValue`, `goodNewsOnly`, and `sourceFilter` from `useSearchParams()` only on first render and never reapplies URL changes to local state.
  - [P2] The article detail page currently turns every fetch failure into "Article not found". `src/frontend/app/article/[id]/page.tsx` sets `notFound` for all rejected article fetches, so transient network errors and backend `5xx` responses are misreported as missing content.
  - [P2] Refresh-path browser coverage is still missing. Current Playwright coverage only proves the seeded cached-browse path.
  - [P2] There is still no repo-owned Playwright npm script. Keep that command-surface decision with Step 16.8 so the refresh-path coverage slice can define the final supported browser-test entrypoint intentionally.
  - [P2] Legacy-boundary guidance is stale. `AGENTS.md` and `READMEOLD.md` still imply root-level v1 runtime files are present, but the checked-out repo root now contains docs/config files plus local env/db artifacts, not the old runtime scripts.
  - [P3] `GET /api/articles/{id}` is more permissive than the processed-only read endpoints. The current frontend only links to processed rows, so this is low-visibility, but the detail contract should be documented or tightened later.
  - [P3] `src/frontend/components/article-card.tsx` can render a blank headline if `was_rewritten` is true while `rewritten_title` is null or empty because the card does not fall back to `original_title`.
  - [P3] The backend refresh pipeline is still lightly tested. The main refresh success test stubs out `process_new_articles_background()`, so request retry behavior, NewsFetcher failure handling, and the false-success path above are not covered by repo-owned tests.
  - [P3] `src/backend/services/refresh_tracker.py` is still in-memory and per-process. That is acceptable for single-process local development but remains non-durable across reloads, restarts, or multiple workers.

## Active phase
Phase 3D: close the remaining safe pre-sign-off slices in priority order. Step 17.1 frontend DX cleanup has already landed in git. The highest implementation priority is now the refresh correctness slice: fix the backend false-success state and the frontend duplicate-refresh acceptance feedback before deeper docs/spec cleanup. After that, fix the frontend URL/error-state regressions from review, then gather trusted-local Phase 3 integration evidence and finish refresh-path browser coverage.

## Ordered checklist
- [x] Re-read repo rules, current plan, top-level docs, all specs, recent git history, current worktree state, and search the repo for issue/review notes on 2026-03-10.
- [x] Re-verify the backend refresh contract, refresh-status endpoint, source normalization behavior, manual integration helper, and backend smoke coverage from source.
- [x] Re-verify the frontend cached-browse-first UX, saved-key handling, refresh polling, Next proxy contract, Playwright harness, and article-detail flow from source.
- [x] Re-run the current validation set: backend smoke tests, backend manual-helper tests, Node version check, frontend lint, frontend typecheck, non-incremental TypeScript check, cached-browse Playwright spec, Turbopack build check, and webpack build check.
- [x] Step 17.1. Land frontend DX cleanup.
- [x] Keep `.nvmrc`, `src/frontend/package.json`, `src/frontend/package-lock.json`, and `src/frontend/next.config.ts` together in that slice; do not stage `README.md`, `loop.sh`, `batch_processor.py`, or spec/doc work with it.
- [x] Decide whether `@playwright/test` belongs in `dependencies` or `devDependencies`, and whether a repo-owned Playwright npm script belongs in Step 17.1 or the later browser-coverage slice.
- [x] Re-run `node -v`, `npm run lint`, `npm run typecheck`, `npx tsc --noEmit --incremental false`, `npm run build`, and `npx next build --webpack` in the Codex sandbox; the Turbopack panic still reproduces there while the webpack build still passes.
- [x] Land the Step 17.1 slice in git as `49274c6` with only the intended frontend DX files.
- [ ] Step 17.5. Fix refresh correctness before docs/spec polish.
- [ ] Make backend refresh failures propagate to `refresh_tracker` as failures instead of a successful zero-article completion when NewsAPI fetches fail after key validation.
- [ ] Make the frontend distinguish duplicate-refresh responses from accepted-key responses so it does not claim the saved key was validated when the backend skipped validation.
- [ ] Add targeted backend regression coverage for the false-success refresh path and the duplicate-refresh frontend/back-end contract.
- [ ] Step 17.6. Fix frontend state/error presentation regressions from code review.
- [ ] Re-sync home-page search/filter/toggle state from URL changes so browser back/forward navigation does not leave controls and results stale.
- [ ] Make the article detail page distinguish `404` from transient fetch failures instead of always rendering "Article not found".
- [ ] Add a safe headline fallback in `src/frontend/components/article-card.tsx` when `rewritten_title` is absent.
- [ ] Add the smallest meaningful frontend or component-level coverage for the URL-sync, detail-error, and headline-fallback cases if they are not fully covered by existing tests.
- [ ] During trusted-local validation, record whether the same Turbopack panic reproduces outside the Codex sandbox.
- [ ] Step 16.7. On a trusted local machine, gather manual Phase 3 integration evidence with a real NewsAPI key.
- [ ] Start the backend and frontend outside Codex. If cached browse is empty, run `python -m src.backend.scripts.seed_manual_integration_data` first.
- [ ] Run `python -m src.backend.scripts.capture_manual_integration_evidence --api-key "$NEWS_API_KEY" --output <report-path>` against the local backend and keep the generated Markdown report.
- [ ] Complete the report's frontend follow-up section from `http://localhost:3000`, covering cached browse without a saved key, refresh with a real key, invalid-key handling, duplicate refresh behavior if observable, refresh-status polling, and the final terminal state.
- [ ] Update this plan with exact observed outcomes and classify each one as `code behavior`, `environment behavior`, `documentation mismatch`, or `still unproven`.
- [ ] Step 16.8. Finish repo-owned browser coverage for the highest-value local flows.
- [ ] Keep `src/frontend/tests/e2e/cached-browse.spec.ts` green against the seeded local backend/frontend pair.
- [ ] Add refresh-path browser coverage only after Step 16.7 evidence exists or a supported backend test double is introduced.
- [ ] Cover the accepted-refresh path, invalid-key UX, and refresh-status polling UX in a deterministic way.
- [ ] Cover the duplicate-refresh path and ensure it does not assert accepted-key feedback unless the current request actually validated the key.
- [ ] Decide whether refresh-status and invalid-key cases belong in Playwright only, a backend-backed test double, or both.
- [ ] Step 17.2. Align top-level docs with the running v2 system.
- [ ] Rewrite the root `README.md` so the v2 app runtime and setup come first and the Ralph loop comes second.
- [ ] Replace `src/frontend/README.md` with real frontend setup, proxy, Playwright, and local validation notes.
- [ ] Remove live v2 setup guidance from `READMEOLD.md` so it is clearly legacy-only.
- [ ] Step 17.3. Reconcile spec drift.
- [ ] Update `specs/OVERVIEW.md` for request-scoped NewsAPI keys, direct OpenAI API usage, SQLite persistence, and the removal of Azure-era runtime assumptions.
- [ ] Update `specs/BACKEND.md` for `/v2/top-headlines`-only fetching, the `country=us` default, typed refresh errors, the 5-second validation timeout, `/api/refresh/status`, duplicate-refresh behavior, the in-memory refresh tracker limits, and normalized source labels across read endpoints.
- [ ] Update `specs/FRONTEND.md` for Next.js `16.1.6`, `next.config.ts`, the current inline onboarding flow, the refresh UX, the seeded Playwright coverage, and the current Turbopack-in-sandbox validation caveat.
- [ ] Decide whether `GET /api/articles/{id}` should remain more permissive than the list/source/stats endpoints or be tightened later, and document that decision in the relevant spec/docs slice.
- [ ] Step 17.4. Resolve the legacy v1 boundary safely.
- [ ] Decide whether legacy runtime scripts are intentionally absent from the working tree, restored into an explicit archive location, or documented as git-history-only reference.
- [ ] Make `READMEOLD.md`, `README.md`, and any operational guidance that mentions root-level legacy files match that decision.
- [ ] If `AGENTS.md` continues to mention root-level legacy files, update that guidance only in the dedicated docs/legacy slice.

## Notes / discoveries that matter for the next loop
- Current dirty worktree state:
  - modified: `IMPLEMENTATION_PLAN.md`
  - modified: `PROMPT_build.md`
  - modified: `PROMPT_plan.md`
- Step 17.1 has already landed in git as `49274c6`: `.nvmrc` pins Node `22.17.0`, `src/frontend/package.json` adds `typecheck` and `engines.node`, `@playwright/test` lives in `devDependencies`, `src/frontend/package-lock.json` matches that package state, and `src/frontend/next.config.ts` sets `turbopack.root` while preserving the `/api/:path*` proxy to `http://localhost:8000/api/:path*`.
- The checklist is intentionally ordered by next-action priority. The next build slice should be Step 17.5 refresh correctness, followed by Step 17.6 frontend URL/error-state fixes; trusted-local Step 16.7 remains required for Phase 3 sign-off, and Step 16.8 stays gated on real refresh evidence or a supported backend test double.
- `/review` on 2026-03-10 found additional correctness gaps that should stay ahead of docs/spec cleanup after Step 17.1 lands: backend refresh false-success reporting, frontend duplicate-refresh accepted-key feedback, browser-history URL/state desync on the home page, detail-page error misclassification, and the missing article-card headline fallback.
- The refresh correctness bugs are linked: the backend currently reports some upstream failures as completed zero-work refreshes, and the frontend currently treats duplicate-refresh completion as proof that the current saved key was accepted even when the backend skipped validation.
- `README.md` already has an uncommitted frontend-validation note. Do not overwrite or stage it accidentally when landing Step 17.1 or later docs work.
- `loop.sh` also has unrelated uncommitted changes. Ignore it unless a later slice explicitly targets loop behavior.
- The checked-out repo root no longer contains legacy runtime scripts such as `run.py`, `search.py`, `web_app.py`, or `batch_processor.py`; current root files are loop/docs/config files plus local `.env` and `newsperspective.db`.
- `git log -- batch_processor.py` points only to legacy-era commits, so its current deletion is not removing active v2 runtime code.
- `src/frontend/playwright.config.mts` seeds a local SQLite database, starts the backend on `127.0.0.1:8000`, starts Next dev on `127.0.0.1:3000`, and writes artifacts under `output/playwright/`.
- `src/frontend/tests/e2e/cached-browse.spec.ts` currently passes and covers cached browse without a saved key, source filtering, search, and article detail against seeded local data.
- Frontend browser coverage currently runs via `npx playwright test tests/e2e/cached-browse.spec.ts`; there is still no repo-owned npm script for Playwright, and that command-surface decision is deferred to Step 16.8.
- Current repo-owned browser coverage does not exercise refresh initiation, duplicate-refresh handling, invalid-key feedback, or browser-history state resync.
- `src/backend/scripts/seed_manual_integration_data.py` provides deterministic processed rows for local manual and browser integration checks.
- `src/backend/scripts/capture_manual_integration_evidence.py` generates the Markdown report for Step 16.7 and already includes explicit frontend follow-up placeholders plus classification guidance.
- `GET /api/articles` returns only rows where `processing_status == "processed"`, so manual and browser integration checks need seeded data or a successful refresh first.
- `GET /api/articles/{id}` does not filter by `processing_status`; the current frontend only reaches detail pages from processed list rows, so this is not user-visible in the normal flow.
- `src/backend/tests/test_api_smoke.py` currently proves refresh preflight behavior and refresh-tracker transitions around mocked background work, but it does not run the real NewsFetcher or ArticleProcessor path that currently converts some upstream failures into false-success completions.
- `npm run build` still fails only in this Codex sandbox because Turbopack tries to create a CSS worker process and bind to a port:
  - `Failed to write app endpoint /page`
  - `creating new process`
  - `binding to a port`
  - `Operation not permitted (os error 1)`
- `npx next build --webpack` passed in this plan run.
- `src/frontend/README.md` is unchanged create-next-app boilerplate and is not usable as current project documentation.
- `READMEOLD.md` still references root-level legacy files that are not present in the checked-out working tree and tells readers to ignore scripts such as `run.py`, `search.py`, `web_app.py`, and `batch_processor.py` that are no longer checked out.
- `AGENTS.md` currently says legacy v1 code still exists in the repo root. That is now a documentation mismatch against the checked-out tree, not a trustworthy description of what is on disk.

## Next recommended build slice
Step 17.5: fix refresh correctness so upstream fetch failures cannot report false success and duplicate refreshes cannot falsely validate the saved key in the UI.

Trusted-local follow-up outside Codex: run Step 16.7 with a real NewsAPI key and update this plan with the generated report outcomes.
