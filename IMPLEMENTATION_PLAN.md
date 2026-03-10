# IMPLEMENTATION_PLAN.md

## PLEASE DO NOT DELETE THIS FILE. Thanks.

## Current status summary and code review
- Recent landed slices in git history confirm the current direction: frontend DX guardrails (`49274c6`), seeded Playwright cached-browse coverage (`efa45d2`), manual integration evidence helper (`0c65e40`), source normalization (`0b8a268`), and the US NewsAPI default (`cc8a629`).
- Re-checked on 2026-03-10 in plan mode. Read `AGENTS.md`, `IMPLEMENTATION_PLAN.md`, `README.md`, `READMEOLD.md`, `src/frontend/README.md`, all files in `specs/`, recent git history, and the backend/frontend source that defines the live v2 contract.
- Searched the repo for repo-local issue tracker files and written review notes. None were found. This file remains the active review record for the next Ralph loop.
- The previous plan had gone stale about Step 17.5 local state. Current worktree state before this planning edit was:
- `src/frontend/app/page.tsx` modified
- `src/backend/tests/test_refresh_processing.py` untracked
- Recent commits already landed the backend refresh-failure handling:
- `0943942` updated `src/backend/services/news_fetcher.py` so hard NewsAPI fetch failures raise `NewsFetchError` instead of quietly ending as an empty successful refresh.
- `80b1a40` updated `src/backend/services/article_processor.py` so `process_new_articles_background()` marks the refresh as failed when `NewsFetchError` escapes.
- Verified backend behavior from source:
- `src/backend/main.py` is the active FastAPI app and mounts only the routers under `src/backend/`.
- `POST /api/refresh` still lives in `src/backend/routers/sources.py`, requires `X-News-Api-Key`, validates it against NewsAPI `GET /v2/top-headlines` with `country=us`, `pageSize=1`, and a 5-second timeout, then starts the background task.
- Duplicate refresh requests still short-circuit before validation and return `{ "status": "processing", "message": "Refresh already in progress." }`.
- `GET /api/refresh/status` still exposes in-memory state from `src/backend/services/refresh_tracker.py`.
- `GET /api/articles`, `GET /api/sources`, and `GET /api/stats` still filter to `processing_status="processed"`.
- `GET /api/articles/{id}` still returns any row by id and does not apply the processed-only filter.
- Verified frontend behavior from source:
- Cached browsing still works without a saved key. The inline `ApiKeySetup` card shows only when no key is stored.
- NewsAPI keys are still stored in `localStorage` via `src/frontend/hooks/use-api-key.ts`.
- Read-only article/source/stats requests do not attach the NewsAPI key. Refresh requests do.
- The home page still polls `/api/refresh/status` every second for up to 120 seconds after refresh starts.
- `src/frontend/app/page.tsx` now suppresses accepted-key feedback and misleading success copy when the refresh response is the duplicate-refresh short-circuit.
- The committed home-page state still seeds `search`, `good_news`, and `source` from `useSearchParams()` only on first render, so browser back/forward can still desynchronise controls and results.
- `src/frontend/app/article/[id]/page.tsx` still maps every fetch failure to the not-found screen.
- `src/frontend/components/article-card.tsx` still prefers `rewritten_title` whenever `was_rewritten` is true, so a null or empty rewritten title can still blank the visible headline.
- Validation re-run in this planning pass:
- `source src/backend/.venv/bin/activate && python -m unittest src.backend.tests.test_api_smoke -v` passed all 14 tests.
- `source src/backend/.venv/bin/activate && python -m unittest src.backend.tests.test_refresh_processing -v` passed 2 regression tests.
- `cd src/frontend && npm run lint` exited 0.
- `cd src/frontend && npm run typecheck` exited 0.
- `source src/backend/.venv/bin/activate && python -m unittest src.backend.tests.test_refresh_processing src.backend.tests.test_api_smoke -v` is not a reliable combined command in this repo because both modules set `DATABASE_URL` at import time for different temp databases. Re-run them as separate commands.
- Validation not re-run in this pass:
- `python -m unittest src.backend.tests.test_manual_integration_evidence -v`
- `cd src/frontend && npm run build`
- `cd src/frontend && npx next build --webpack`
- `cd src/frontend && npx playwright test tests/e2e/cached-browse.spec.ts`
- Carry-forward evidence from the earlier 2026-03-10 plan pass still stands until someone rechecks it:
- `cd src/frontend && npm run build` failed in the Codex sandbox because Turbopack tried to create a CSS worker process and bind to a port, which the sandbox blocked with `Operation not permitted`.
- `cd src/frontend && npx next build --webpack` passed in that earlier pass.
- Managed Playwright startup was blocked in that earlier pass because local processes were already listening on `127.0.0.1:8000` and `127.0.0.1:3000`. That was environment behavior, not fresh app evidence.
- Current code review findings, highest risk first:
- [P1] Step 17.5 is still not fully landed. The remaining frontend duplicate-refresh UX fix is only in the dirty worktree, and `src/backend/tests/test_refresh_processing.py` is still untracked.
- [P1] The untracked refresh regression file is stronger than the stale plan recorded, but it still does not drive the concrete `NewsFetcher` failure branch that motivated `NewsFetchError`; one test patches `NewsFetcher.fetch_all_categories`, and the other patches `ArticleProcessor.process_new_articles`.
- [P1] Trusted-machine Phase 3 manual integration evidence is still missing. The helper script and helper tests exist, but there is still no recorded run against real local servers with a real NewsAPI key.
- [P1] Top-level docs and specs still drift from the running v2 app:
- `README.md` is still Ralph-loop-first instead of app-first.
- `READMEOLD.md` still contains live v2 backend setup guidance even though it is labeled legacy.
- `READMEOLD.md` still tells readers to ignore old root scripts such as `batch_processor.py`, `run.py`, `search.py`, and `web_app.py`, but those files are not present in the checked-out tree.
- `AGENTS.md` still says legacy v1 code exists in the repo root, which no longer matches the checked-out tree.
- `specs/OVERVIEW.md` still describes Azure-era architecture and stale NewsAPI assumptions.
- `specs/BACKEND.md` still describes `/v2/everything`, UK-focused behavior, and older refresh assumptions. It omits `/api/refresh/status`, duplicate-refresh behavior, typed refresh errors, the 5-second validation timeout, and the current source-normalization contract.
- `specs/FRONTEND.md` still describes fullscreen first-visit onboarding, `next.config.js`, and older Next.js assumptions instead of the current inline cached-browse-first flow on Next.js `16.1.6` with `next.config.ts`.
- [P2] Browser back/forward can still desynchronise the URL from the frontend search/filter/toggle state.
- [P2] The article detail page still turns every fetch failure into `Article not found`.
- [P2] Refresh-path browser coverage is still missing. The only repo-owned Playwright spec still proves the seeded cached-browse path.
- [P3] `src/frontend/components/article-card.tsx` can still render a blank headline if `was_rewritten` is true while `rewritten_title` is null or empty.
- [P3] `GET /api/articles/{id}` is still more permissive than the processed-only list/source/stats endpoints.
- [P3] `src/backend/services/refresh_tracker.py` is still in-memory and per-process.

## Active phase
Phase 3D: finish the remaining refresh-correctness landing slice, then gather trusted-machine integration evidence before broader frontend cleanup and docs/spec alignment. The backend refresh-failure behavior is already present in tracked source; the next build loop should keep scope narrow and finish the remaining local UX/proof work before moving on.

## Ordered checklist
- [x] Re-read repo rules, current plan, README context, all specs, recent git history, and the live backend/frontend source on 2026-03-10.
- [x] Search the repo for repo-local issue tracker files and written code-review notes. None were found.
- [x] Re-check the worktree and recent commits so the plan reflects current local state instead of the stale prior Step 17.5 notes.
- [x] Re-run the smallest current validation: backend smoke tests, backend refresh-processing tests, frontend lint, and frontend typecheck.
- [ ] Step 17.5. Finish and validate the remaining refresh-correctness slice from the current dirty worktree.
- [ ] Review and finalize the local edit in `src/frontend/app/page.tsx` so duplicate-refresh responses do not create accepted-key feedback or misleading success messaging.
- [ ] Decide whether duplicate-refresh UI proof belongs in this slice now or must explicitly wait for Step 16.8 Playwright coverage, and record that decision when the slice lands.
- [ ] Convert `src/backend/tests/test_refresh_processing.py` from local-only coverage into repo-owned proof.
- [ ] Extend the regression proof so it reaches the concrete fetcher failure path that motivated `NewsFetchError`, not only a mocked `process_new_articles()` raise or a mocked `fetch_all_categories()` raise.
- [ ] Re-run `python -m unittest src.backend.tests.test_refresh_processing -v`, `python -m unittest src.backend.tests.test_api_smoke -v`, `cd src/frontend && npm run lint`, and `cd src/frontend && npm run typecheck` after Step 17.5 is finalized.
- [ ] Step 16.7. On a trusted local machine, gather manual Phase 3 integration evidence with a real NewsAPI key.
- [ ] Start backend and frontend outside Codex, or use the Docker app stack if that is the intended supported local path.
- [ ] If cached browse is empty, seed deterministic data first with `python -m src.backend.scripts.seed_manual_integration_data`.
- [ ] Run `python -m src.backend.scripts.capture_manual_integration_evidence --api-key "$NEWS_API_KEY" --output <report-path>` and keep the generated Markdown report.
- [ ] Complete the report's frontend follow-up section from `http://localhost:3000`, covering cached browse without a saved key, refresh with a real key, invalid-key handling, duplicate-refresh behavior if observable, refresh-status polling, and the final terminal state.
- [ ] Update this plan with exact observed outcomes and classify each one as `code behavior`, `environment behavior`, `documentation mismatch`, or `still unproven`.
- [ ] Step 17.6. Fix the remaining frontend state and error regressions.
- [ ] Re-sync home-page search/filter/toggle state from URL changes so browser back/forward keeps controls and results in sync.
- [ ] Make the article detail page distinguish `404` from transient fetch failures instead of always showing the not-found screen.
- [ ] Add a safe headline fallback in `src/frontend/components/article-card.tsx` when `was_rewritten` is true but `rewritten_title` is empty.
- [ ] Add the smallest meaningful coverage for the URL-sync, detail-error, and headline-fallback cases if existing tests do not already prove them.
- [ ] Step 16.8. Finish repo-owned browser coverage for the highest-value refresh flows.
- [ ] Keep `src/frontend/tests/e2e/cached-browse.spec.ts` green against the supported local test path.
- [ ] Add deterministic browser coverage for accepted refresh, invalid-key UX, refresh-status polling UX, and duplicate-refresh messaging.
- [ ] Decide in this slice whether a repo-owned Playwright npm script should exist. Do not add it accidentally in an earlier slice.
- [ ] Step 17.2. Align top-level docs with the running v2 app.
- [ ] Rewrite the root `README.md` so the v2 app runtime and setup come first, the Ralph loop comes second, and the supported local and Docker flows are explicit.
- [x] Keep `src/frontend/README.md` as the active frontend runtime, proxy, Playwright, and Docker guide unless the frontend code changes again.
- [ ] Remove live v2 setup guidance from `READMEOLD.md` so it is clearly legacy-only.
- [ ] Step 17.3. Reconcile spec drift.
- [ ] Update `specs/OVERVIEW.md` for request-scoped NewsAPI keys, direct OpenAI API usage, SQLite persistence, and the removal of Azure-era runtime assumptions.
- [ ] Update `specs/BACKEND.md` for `/v2/top-headlines`-only fetching, `country=us` defaults, typed refresh errors, the 5-second validation timeout, `/api/refresh/status`, duplicate-refresh behavior, the in-memory refresh tracker limits, and current source normalization behavior.
- [ ] Update `specs/FRONTEND.md` for Next.js `16.1.6`, `next.config.ts`, the current inline onboarding flow, refresh UX, refresh polling, the Docker local path, and the current validation caveats.
- [ ] Decide whether `GET /api/articles/{id}` should remain more permissive than the processed-only list/source/stats endpoints or be tightened later, and document that decision in the relevant spec/docs slice.
- [ ] Step 17.4. Resolve the legacy v1 boundary safely.
- [ ] Decide whether legacy runtime files are intentionally absent from the working tree, restored into an explicit archive location, or documented as git-history-only reference.
- [ ] Make `READMEOLD.md`, `README.md`, and `AGENTS.md` match that legacy decision.

## Notes / discoveries that matter for the next loop
- The previous plan was stale about Step 17.5 local state. `src/backend/services/news_fetcher.py` and `src/backend/services/article_processor.py` are no longer dirty; the refresh-failure handling is already present in tracked source via recent commits.
- Current local Step 17.5 files are only:
- `src/frontend/app/page.tsx`
- `src/backend/tests/test_refresh_processing.py` (still untracked)
- `src/backend/tests/test_refresh_processing.py` now contains two passing tests:
- One proves `ArticleProcessor.process_new_articles()` propagates `NewsFetchError` thrown by the fetcher boundary.
- One proves `process_new_articles_background()` marks refresh status as failed when `NewsFetchError` escapes.
- That file still does not hit the concrete `NewsFetcher` failure branch inside the fetcher implementation itself. The plan should continue to treat that as the remaining backend proof gap until a build slice closes it or explicitly defers it with rationale.
- `src/backend/tests/test_api_smoke.py` already proves the duplicate-refresh API contract and the structured refresh validation errors. The open frontend gap is UI handling and browser-level proof.
- `src/frontend/lib/api.ts` still throws a generic error for `fetchArticle()`. That is why the detail page cannot distinguish `404` from `5xx` or network failure without a small API-client or page-state change.
- `src/frontend/components/article-card.tsx` still uses `article.was_rewritten ? article.rewritten_title : article.original_title`, so a missing `rewritten_title` can still blank the visible headline.
- `src/backend/services/refresh_tracker.py` is in-memory only. Refresh state is per process and resets on restart.
- `README.md` is still a Ralph-loop document first. It does not yet work as the main app runtime guide.
- `READMEOLD.md` still mixes legacy framing with live v2 backend setup instructions and references files that are absent from the current root tree.
- `AGENTS.md` still says legacy v1 code exists in the repo root, which does not match the checked-out tree.
- `specs/OVERVIEW.md`, `specs/BACKEND.md`, and `specs/FRONTEND.md` still describe older architecture and UX assumptions. Use live source over specs until Step 17.3 lands.
- `npm run lint` and `npm run typecheck` exited 0 in this pass, but the shell printed `nvm` usage text before command output. Treat that as shell-init noise unless it starts affecting exit codes or CI.

## Next recommended build slice
Step 17.5: continue from the current local edits in `src/frontend/app/page.tsx` and `src/backend/tests/test_refresh_processing.py`. Keep the slice narrow. Land the duplicate-refresh UX fix, turn the untracked backend regression file into repo-owned coverage, and strengthen that proof so it exercises a real fetcher failure branch rather than only mocked higher-level raises. Then re-run `python -m unittest src.backend.tests.test_refresh_processing -v`, `python -m unittest src.backend.tests.test_api_smoke -v`, `cd src/frontend && npm run lint`, and `cd src/frontend && npm run typecheck`. Do not mix in Step 17.6, manual integration, or docs work.

- FIX THIS AS A MATTER OF URGENCY.[P1] Sanitize request errors before exposing refresh failure status — /Users/tombutler/Repos/NewsPerspective/src/backend/services/news_fetcher.py:96-97 requests includes the full request URL in many RequestException/HTTPError messages, and this request sends the NewsAPI key as an apiKey query parameter. With this change, those raw exception strings are wrapped in NewsFetchError and then surfaced verbatim via refresh_tracker.mark_failed(str(exc)), so any 4xx/5xx during category fetch can leak the user's NewsAPI key through the unauthenticated /api/refresh/ status response (and logs).