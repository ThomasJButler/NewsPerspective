# IMPLEMENTATION_PLAN.md

## Current status summary and code review
- Re-checked on 2026-03-10. The active v2 app is still the FastAPI backend in `src/backend/` and the Next.js frontend in `src/frontend/`.
- Read again for this planning pass: `AGENTS.md`, `README.md`, `READMEOLD.md`, `.env.template`, all files in `specs/`, and the main backend/frontend source that drives refresh, browsing, source filters, and settings.
- Searched for repo-local issue or review notes. None were found beyond the loop prompts and the current plan. Recent repo history is still:
  - `c865189` Add env template, relocate backend reqs, update docs
  - `a030bfa` Update docs and backend setup
  - `eb72797` Complete Phase 2.5: Quality fixes QF-1 through QF-7
- Fresh validation on 2026-03-10:
  - `python3 -m unittest src.backend.tests.test_api_smoke -v` passed all 12 tests after the Step 16.2 backend contract change.
  - `npm run lint` passed in `src/frontend/`.
  - `npx tsc --noEmit` passed in `src/frontend/`.
  - `npm run lint` passed again in `src/frontend/` after the Step 16.3 frontend refresh-contract update.
  - `npx tsc --noEmit` passed again in `src/frontend/` after the Step 16.3 frontend refresh-contract update.
  - `npm run build` still fails in this sandbox with the known Turbopack port-bind panic: `Failed to write app endpoint /page` -> `creating new process` -> `binding to a port` -> `Operation not permitted (os error 1)`.
- Current code review findings, highest risk first:
  - [P2] `GET /api/stats` still counts distinct raw `Article.source_name` values, not the normalized source label contract already used by `/api/articles` and `/api/sources`.
  - [P2] Backend smoke coverage now proves structured refresh errors and timeout handling, but it still does not prove successful refresh completion.
  - [P2] Real Phase 3 integration evidence is still missing because this sandbox cannot host the app on localhost or make the full outbound validation path reliable.
  - [P3] DX and docs still drift from the running app: no frontend `typecheck` script, no repo-owned Node version pin, stock `src/frontend/README.md`, loop-first root `README.md`, and `READMEOLD.md` still contains live v2 setup steps.
  - [P3] Spec drift is still real:
  - `specs/OVERVIEW.md` still says Azure OpenAI and says the app only needs `NEWS_API_KEY`.
  - `specs/BACKEND.md` still mentions `/v2/everything`, misses `/api/refresh/status`, and does not describe refresh tracking or source normalization.
  - `specs/FRONTEND.md` still describes a first-visit full-screen onboarding flow as the main path and still names older config files instead of the current Next.js 16 + `next.config.ts` + Tailwind v4 setup.
- The current product behavior still matches these v2 rules:
  - Refresh requires the user key in `X-News-Api-Key`.
  - Read endpoints work without a key and show cached data only.
  - AI still runs once per article and returns sentiment, rewrite decision/output, TLDR, and good-news data.
  - `OPENAI_API_KEY` is optional at runtime and falls back to neutral defaults.

## Active phase
Phase 3B. Finish the refresh contract first. Then get real integration evidence. After that, clean up DX, docs, and the legacy boundary.

## Ordered checklist
- [x] Re-read the repo rules, current plan, README context, specs, and the backend/frontend files that drive v2 behavior.
- [x] Search for repo-local issues and recent code review notes, and re-check recent commits for planning context.
- [x] Re-run the smallest useful validations: backend smoke tests, frontend lint, frontend TypeScript, and frontend build.
- [x] Confirm the current v2 behavior in code: request-scoped NewsAPI key, cached browse without a key, inline onboarding, normalized sources, and refresh status polling.
- [x] Step 16.1. Make duplicate refresh claiming atomic in `src/backend/services/refresh_tracker.py` and `src/backend/routers/sources.py`, and cover the regression in `src/backend/tests/test_api_smoke.py`.
- [x] Step 16.2. Tighten the backend refresh error contract in `src/backend/routers/sources.py` and `src/backend/schemas.py`.
- [x] Add an explicit timeout to the NewsAPI key validation call.
- [x] Return machine-readable refresh errors instead of plain string `detail` values.
- [x] Distinguish at least these cases: missing key, invalid key, upstream timeout, and upstream transport failure.
- [x] Keep this slice backend-only. Do not change frontend handling yet.
- [x] Step 16.3. Update the frontend refresh flow in `src/frontend/lib/api.ts`, `src/frontend/types/article.ts`, `src/frontend/app/page.tsx`, and the existing key UI components.
- [x] Consume the structured backend contract instead of regex parsing.
- [x] Preserve cached browsing and the current inline no-key onboarding flow.
- [x] Stop showing an in-progress refresh as a generic failure when polling reaches 120 seconds.
- [ ] Step 16.4. Align `GET /api/stats` so `sources_count` uses the same normalized source label contract as `/api/articles` and `/api/sources`.
- [ ] Step 16.5. Extend the smallest useful regression coverage for Steps 16.2 to 16.4.
- [x] Add backend assertions for structured refresh errors and timeout handling.
- [x] Add or update frontend checks only if the structured contract reaches the client in this phase.
- [ ] Re-run `python3 -m unittest src.backend.tests.test_api_smoke -v`, `npm run lint`, and `npx tsc --noEmit`.
- [ ] Step 16.6. Run the remaining manual Phase 3 integration checks on a machine that allows localhost listeners and outbound network access.
- [ ] Seed data first with `python -m src.backend.scripts.seed_manual_integration_data` if cached browse needs data.
- [ ] Record results for: cached browse without a key, successful refresh with a real key, invalid-key handling, duplicate refresh behavior, refresh-status polling during a long refresh, and final completion state.
- [ ] Step 17.1. Turn the current smoke-first testing habit into a real v2 test plan and first implementation pass.
- [ ] Name the backend, frontend, and integration surfaces that still need coverage.
- [ ] Add the highest-value missing tests first and record what still remains.
- [ ] Step 17.2. Add a repo-owned frontend type-check command such as `npm run typecheck`.
- [ ] Step 17.3. Pin or clearly document the supported Node runtime in a repo-owned file such as `.nvmrc`, `.node-version`, `.tool-versions`, or `package.json` `engines`.
- [ ] Step 17.4. Rewrite the root `README.md` so it explains the v2 product/runtime first and the Ralph loop second. Replace the stock `src/frontend/README.md` with real frontend setup notes.
- [ ] Step 17.5. Reconcile spec drift in `specs/OVERVIEW.md`, `specs/BACKEND.md`, and `specs/FRONTEND.md`.
- [ ] Document request-scoped `X-News-Api-Key`, optional `OPENAI_API_KEY`, `/api/refresh/status`, category-based `/v2/top-headlines` fetching, Next.js 16.1.6, `next.config.ts`, Tailwind v4, and the current inline onboarding flow.
- [ ] Step 17.6. Remove active v2 setup guidance from `READMEOLD.md` so it is clearly legacy-only.
- [ ] Step 17.7. Decide what to do with the remaining root-level v1 files and the in-progress local deletions. Do not move or restore anything until Steps 16.2 to 17.6 are stable.
- [ ] Step 17.8. If Step 17.7 changes the legacy layout, update docs and ignore rules so legacy files do not confuse v2 setup.

## Notes / discoveries that matter for the next loop
- The worktree is already dirty. Do not revert unrelated WIP. That includes active backend/frontend work and in-progress root legacy deletions.
- Root legacy cleanup is already partly in motion in the worktree:
  - Deleted locally: `azure_ai_language.py`, `azure_document_intelligence.py`, `logger_config.py`, `run.py`, `search.py`, `web_app.py`
  - Still present at repo root: `batch_processor.py`
- `src/backend/services/refresh_tracker.py` is in-memory and per-process. It is fine for one local dev server, but it is not durable across reloads, restarts, or multiple workers.
- `POST /api/refresh` now validates the NewsAPI key with a 5-second timeout and returns structured `detail` payloads with codes for `missing_api_key`, `invalid_api_key`, `upstream_timeout`, and `upstream_transport_failure`.
- `src/backend/services/article_processor.py` already owns terminal refresh states by calling `mark_completed()` and `mark_failed()`. The next backend slice should stay focused on the request/response contract, not widen into a background-job redesign.
- `GET /api/articles` still returns only `processing_status == "processed"` rows. Manual browse checks need seeded data or a successful refresh first.
- `src/frontend/lib/api.ts` now throws a typed `RefreshRequestError` with `detail.code` and `detail.message`, and `src/frontend/app/page.tsx` now branches on those codes instead of regex parsing.
- `src/frontend/app/page.tsx` now treats the 120-second refresh-status polling limit as "still processing" rather than as a generic failure toast.
- `src/frontend/app/page.tsx` renders the inline `ApiKeySetup` card when there is no saved key. The full-screen variant still exists in the component, but it is not the active home-page path.
- `src/frontend/package.json` still has no `typecheck` script.
- There is still no `.nvmrc`, `.node-version`, or `.tool-versions` file in the repo.
- `src/frontend/next.config.ts` still proxies `/api/:path*` to `http://localhost:8000/api/:path*`, so real frontend integration still depends on a separate backend listener on port `8000`.
- This sandbox still cannot bind localhost ports needed for full app runs, and it also triggers the Turbopack port-bind panic during `next build`.

Simple
- What: Manual integration is still blocked here, even though the code inspection and smoke checks are useful.
- Why: This environment can run small unit-style checks, but it cannot host the full app the same way a normal local machine can.
- CS idea: Unit tests check pieces in isolation. Integration testing checks whether the pieces still work when they talk to each other over real process and network boundaries.
- Next: Update the frontend refresh flow to consume the new backend error contract, then run the remaining Phase 3 checks on a machine with normal localhost and network access.

## Next recommended build slice
Step 16.4. Align `GET /api/stats` so `sources_count` uses the same normalized source label contract as `/api/articles` and `/api/sources`.

Keep this slice backend-only, then extend the smallest useful regression coverage so the normalized stats contract is proven in smoke tests.
