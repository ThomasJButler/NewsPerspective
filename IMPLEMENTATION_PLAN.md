# IMPLEMENTATION_PLAN.md

## PLEASE DO NOT DELETE THIS FILE. Thanks.

## Active status
- Updated on 2026-03-10 after re-aligning `specs/BACKEND.md` with the current v2 refresh/status/runtime behavior.
- Fully completed work was moved to `specs/completedarchive/2026-03-10-implementation-completed-archive.md`.
- Active phase: Phase 3D. The remaining work is trusted-machine evidence, refresh-path browser coverage, the remaining frontend-spec alignment, header branding, and the remaining backend policy/test decisions.

## Open findings
- [P1] Trusted-machine manual integration evidence is still missing for the current v2 refresh flow.
- [P1] `specs/FRONTEND.md` still drifts from the running app and is now the main remaining top-level docs/spec alignment gap.
- [P2] Refresh-path browser coverage is still missing beyond the cached-browse seeded/spec-stub paths.
- [P3] `GET /api/articles/{id}` is still more permissive than the processed-only list, source, and stats endpoints.
- [P3] The backend refresh pipeline is still lightly tested for retry and multi-category partial-failure behavior.
- [P3] `src/backend/services/refresh_tracker.py` is still in-memory and per-process.

## Remaining work by area

### Frontend changes
- [ ] Replace the empty header slot visible on mobile and desktop with intentional branding actions, including links to `https://github.com/ThomasJButler` and `https://buymeacoffee.com/ojrwoqkgmv`.
- [ ] Make sure the GitHub and Buy Me a Coffee links work cleanly across desktop and mobile layouts and do not crowd the existing refresh, theme, settings, or search controls.
- [x] Re-sync the home-page search, source, and good-news controls from URL changes so browser back/forward keeps controls and results aligned.
- [x] Make the article detail page distinguish `404` from transient fetch or network failures instead of always rendering the not-found state.
- [x] Add a safe visible-title fallback in `src/frontend/components/article-card.tsx` when a rewritten headline is missing or empty.
- [x] Add the smallest meaningful coverage for the URL-sync, detail-error, and headline-fallback paths.

### Backend changes
- Decide whether `GET /api/articles/{id}` should remain more permissive than the processed-only list, source, and stats endpoints, or be tightened.
- Add focused backend coverage for refresh success-path behavior that is still stubbed today, especially retry and multi-category partial-failure handling.

### Testing and evidence
- On a trusted local machine, gather manual Phase 3 integration evidence with a real NewsAPI key.
- Start backend and frontend outside Codex, or use the supported Docker app stack.
- If cached browse is empty, seed deterministic data with `python -m src.backend.scripts.seed_manual_integration_data`.
- Run `python -m src.backend.scripts.capture_manual_integration_evidence --api-key "$NEWS_API_KEY" --output <report-path>` and keep the generated Markdown report.
- Complete the report's frontend follow-up section from `http://localhost:3000`, covering cached browse without a saved key, refresh with a real key, invalid-key handling, duplicate-refresh behavior if observable, refresh-status polling, and the final terminal state.
- Update this plan with exact observed outcomes and label each one as `code behavior`, `environment behavior`, `documentation mismatch`, or `still unproven`.
- Keep `src/frontend/tests/e2e/cached-browse.spec.ts` green against the supported local test path.
- Add deterministic browser coverage for accepted refresh, invalid-key UX, refresh-status polling UX, and duplicate-refresh messaging.
- Decide in that browser-coverage slice whether a repo-owned Playwright npm script should exist.

### Docs and specs
- [x] Rewrite `README.md` so the v2 app runtime and setup come first, the Ralph loop comes second, and the supported local and Docker flows are explicit.
- [x] Remove live v2 setup guidance from `READMEOLD.md` so it is clearly legacy-only.
- [x] Update `specs/OVERVIEW.md` for request-scoped NewsAPI keys, direct OpenAI API usage, SQLite persistence, and the removal of Azure-era runtime assumptions.
- [x] Update `specs/BACKEND.md` for `/v2/top-headlines`, `country=us`, typed refresh errors, the 5-second validation timeout, `/api/refresh/status`, duplicate-refresh behavior, in-memory refresh tracking limits, and current source normalization.
- [ ] Update `specs/FRONTEND.md` for Next.js `16.1.6`, `next.config.ts`, the inline onboarding flow, refresh UX, refresh polling, Docker local flow, and current validation caveats.

### Architecture and repo boundary
- Decide whether legacy v1 runtime files are intentionally absent, restored into an explicit archive location, or documented as git-history-only reference.
- Make `READMEOLD.md`, `README.md`, and `AGENTS.md` match that legacy-boundary decision.
- Keep the per-process nature of `src/backend/services/refresh_tracker.py` documented until it is intentionally changed.

## Validation notes
- Last confirmed on 2026-03-10 for the `specs/BACKEND.md` docs/spec slice: content was cross-checked against `src/backend/main.py`, `src/backend/routers/articles.py`, `src/backend/routers/sources.py`, `src/backend/services/news_fetcher.py`, `src/backend/services/article_processor.py`, `src/backend/services/refresh_tracker.py`, `src/backend/utils/source_normalization.py`, `src/backend/schemas.py`, `src/backend/tests/test_api_smoke.py`, and `src/backend/tests/test_refresh_processing.py`.
- Re-ran on 2026-03-10 after the `specs/BACKEND.md` alignment slice: `python -m unittest src.backend.tests.test_api_smoke -v` and `python -m unittest src.backend.tests.test_refresh_processing -v` both passed.
- Last confirmed on 2026-03-10 for the `READMEOLD.md` and `specs/OVERVIEW.md` docs/spec slice: content was cross-checked against `README.md`, `src/backend/main.py`, `src/backend/config.py`, `src/backend/routers/articles.py`, `src/backend/routers/sources.py`, `src/backend/services/article_processor.py`, `src/backend/services/ai_service.py`, and `src/frontend/package.json`.
- Last confirmed on 2026-03-10 for the `README.md` rewrite: repo paths, commands, and Docker references were cross-checked against `.env.template`, `.nvmrc`, `src/backend/main.py`, `src/backend/config.py`, `src/backend/routers/sources.py`, `src/frontend/package.json`, `src/frontend/next.config.ts`, `src/frontend/compose.yaml`, and `src/frontend/scripts/docker-start-app.sh`.
- Last confirmed on 2026-03-10: `python -m unittest src.backend.tests.test_api_smoke -v`, `python -m unittest src.backend.tests.test_refresh_processing -v`, `cd src/frontend && npm run lint`, `cd src/frontend && npm run typecheck`, and `cd src/frontend && npx playwright test tests/e2e/cached-browse.spec.ts` all passed.
- Do not rely on `python -m unittest src.backend.tests.test_refresh_processing src.backend.tests.test_api_smoke -v` as a combined command in this repo. Both modules set `DATABASE_URL` at import time for different temp databases.
- `cd src/frontend && npm run build` was previously blocked in the sandbox because Turbopack tried to bind a worker port. `cd src/frontend && npx next build --webpack` passed in the earlier 2026-03-10 validation pass.
- Managed Playwright startup was previously blocked because local processes were already listening on `127.0.0.1:8000` and `127.0.0.1:3000`. Treat that as environment behavior until it is rechecked.
- In this Codex environment, Playwright also required a one-time `cd src/frontend && npx playwright install chromium` before the cached-browse spec could launch Chromium.
- This Codex environment does not currently expose `NEWS_API_KEY`, so the real-key portion of Step 18.1 remains a trusted-machine/manual slice rather than a Codex-run validation step.

## Next recommended build slice
- Step 18.1 if running on a trusted local machine with a real `NEWS_API_KEY`: gather the missing Phase 3 refresh evidence and record the exact observed outcomes in this plan. Otherwise, continue the remaining P1 docs/spec alignment work with `specs/FRONTEND.md`.
