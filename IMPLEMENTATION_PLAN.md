# IMPLEMENTATION_PLAN.md

## PLEASE DO NOT DELETE THIS FILE. Thanks.

## Active status
- Updated on 2026-03-10 after reviewing `AGENTS.md`, the current plan, `specs/`, and recent git history.
- Fully completed work was moved to `specs/completedarchive/2026-03-10-implementation-completed-archive.md`.
- Active phase: Phase 3D. The remaining work is frontend correctness, trusted-machine evidence, browser coverage, and docs/spec alignment.

## Open findings
- [P1] Trusted-machine manual integration evidence is still missing for the current v2 refresh flow.
- [P1] Top-level docs and specs still drift from the running app, especially `README.md`, `READMEOLD.md`, `AGENTS.md`, `specs/OVERVIEW.md`, `specs/BACKEND.md`, and `specs/FRONTEND.md`.
- [P2] Browser back/forward can still desynchronise the home-page URL from search and filter state.
- [P2] The article detail page still turns every fetch failure into `Article not found`.
- [P2] Refresh-path browser coverage is still missing beyond the seeded cached-browse spec.
- [P3] `src/frontend/components/article-card.tsx` can still render a blank headline when `was_rewritten` is true but `rewritten_title` is empty.
- [P3] `GET /api/articles/{id}` is still more permissive than the processed-only list, source, and stats endpoints.
- [P3] The backend refresh pipeline is still lightly tested for retry and multi-category partial-failure behavior.
- [P3] `src/backend/services/refresh_tracker.py` is still in-memory and per-process.

## Remaining work by area

### Frontend changes
- Replace the empty header slot visible on mobile and desktop with intentional branding actions, including links to `https://github.com/ThomasJButler` and `https://buymeacoffee.com/ojrwoqkgmv`.
- Make sure the GitHub and Buy Me a Coffee links work cleanly across desktop and mobile layouts and do not crowd the existing refresh, theme, settings, or search controls.
- Re-sync the home-page search, source, and good-news controls from URL changes so browser back/forward keeps controls and results aligned.
- Make the article detail page distinguish `404` from transient fetch or network failures instead of always rendering the not-found state.
- Add a safe visible-title fallback in `src/frontend/components/article-card.tsx` when a rewritten headline is missing or empty.
- Add the smallest meaningful coverage for the URL-sync, detail-error, and headline-fallback paths if current tests do not already prove them.

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
- Rewrite `README.md` so the v2 app runtime and setup come first, the Ralph loop comes second, and the supported local and Docker flows are explicit.
- Remove live v2 setup guidance from `READMEOLD.md` so it is clearly legacy-only.
- Update `specs/OVERVIEW.md` for request-scoped NewsAPI keys, direct OpenAI API usage, SQLite persistence, and the removal of Azure-era runtime assumptions.
- Update `specs/BACKEND.md` for `/v2/top-headlines`, `country=us`, typed refresh errors, the 5-second validation timeout, `/api/refresh/status`, duplicate-refresh behavior, in-memory refresh tracking limits, and current source normalization.
- Update `specs/FRONTEND.md` for Next.js `16.1.6`, `next.config.ts`, the inline onboarding flow, refresh UX, refresh polling, Docker local flow, and current validation caveats.

### Architecture and repo boundary
- Decide whether legacy v1 runtime files are intentionally absent, restored into an explicit archive location, or documented as git-history-only reference.
- Make `READMEOLD.md`, `README.md`, and `AGENTS.md` match that legacy-boundary decision.
- Keep the per-process nature of `src/backend/services/refresh_tracker.py` documented until it is intentionally changed.

## Validation notes
- Last confirmed on 2026-03-10: `python -m unittest src.backend.tests.test_api_smoke -v`, `python -m unittest src.backend.tests.test_refresh_processing -v`, `cd src/frontend && npm run lint`, and `cd src/frontend && npm run typecheck` all passed.
- Do not rely on `python -m unittest src.backend.tests.test_refresh_processing src.backend.tests.test_api_smoke -v` as a combined command in this repo. Both modules set `DATABASE_URL` at import time for different temp databases.
- `cd src/frontend && npm run build` was previously blocked in the sandbox because Turbopack tried to bind a worker port. `cd src/frontend && npx next build --webpack` passed in the earlier 2026-03-10 validation pass.
- Managed Playwright startup was previously blocked because local processes were already listening on `127.0.0.1:8000` and `127.0.0.1:3000`. Treat that as environment behavior until it is rechecked.

## Next recommended build slice
- Step 17.6: fix the remaining frontend state and error presentation regressions, then add the smallest meaningful coverage for those paths before returning to manual evidence and docs/spec alignment.
