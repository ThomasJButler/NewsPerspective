# IMPLEMENTATION_PLAN.md

## 1. Current status summary and code review
- Updated on 2026-03-11 after completing slice 18.6, re-reading `AGENTS.md`, `IMPLEMENTATION_PLAN.md`, `specs/BACKEND.md`, `src/backend/services/news_fetcher.py`, `src/backend/services/article_processor.py`, and `src/backend/tests/test_refresh_processing.py`, and adding backend refresh regression coverage for retry exhaustion and fail-fast category fetch behavior.
- No repo-local issue tracker or written code-review file was found. The findings below come from this planning pass and the current code.
- [P2] Fresh execution evidence for the new refresh-path Playwright spec is still blocked in this Codex sandbox. `src/frontend/tests/e2e/refresh-path.spec.ts` now covers accepted refresh, invalid-key UX, duplicate-refresh attach behavior, polling, and timeout messaging, but Chromium launch fails here before the first page opens.
- [P2] Trusted-machine Phase 3 refresh evidence is still missing for the real-key path. The helper script and helper tests exist, but this Codex environment still does not expose `NEWS_API_KEY`.
- [P3] `src/backend/services/refresh_tracker.py` is still in-memory and per-process. This still matches the current spec. It stays a documented limitation, not a new architecture task.
- Fresh validation on 2026-03-11:
- `source src/backend/.venv/bin/activate && python3 -m unittest src.backend.tests.test_api_smoke -v` passed.
- `source src/backend/.venv/bin/activate && python3 -m unittest src.backend.tests.test_refresh_processing -v` passed.
- `source src/backend/.venv/bin/activate && python3 -m unittest src.backend.tests.test_manual_integration_evidence -v` passed.
- `source src/backend/.venv/bin/activate && python3 -m unittest src.backend.tests.test_api_smoke -v` passed again after slice 18.1 tightened article-detail reads to processed rows only and added `pending`/`failed` detail regressions.
- `cd src/frontend && npm run lint` passed.
- `cd src/frontend && npm run typecheck` passed.
- `cd src/frontend && npx playwright test tests/e2e/cached-browse.spec.ts` failed before test execution with `Error: http://127.0.0.1:8000/api/stats is already used...`.
- `lsof -nP -iTCP:3000,8000 -sTCP:LISTEN` during that run showed Python already listening on `127.0.0.1:8000` and `node` already listening on `3000`. That is environment behavior, not a proven app regression.
- `cd src/frontend && ./node_modules/.bin/eslint tests/e2e/refresh-path.spec.ts` passed after slice 18.2 added deterministic refresh-path coverage.
- `cd src/frontend && npm run typecheck` passed again after slice 18.2.
- `cd src/frontend && PLAYWRIGHT_SKIP_WEBSERVER=1 npx playwright test tests/e2e/refresh-path.spec.ts` failed in this sandbox before app execution because Chromium exited with `bootstrap_check_in ... Permission denied (1100)`.
- `cd src/frontend && npm run dev -- --hostname 127.0.0.1 --port 3100` also failed in this sandbox with `listen EPERM`, so local alternate-port browser validation could not be bootstrapped here.
- `cd src/frontend && npm run test:e2e:reuse -- --list` passed after slice 18.3 and listed both maintained e2e specs without trying to claim local ports.
- `cd src/frontend && npm run typecheck` passed again after slice 18.3.
- `rg -n "removed on 2026-03-10|removed from the checked-out repo on 2026-03-10|git history|archived legacy docs" AGENTS.md README.md READMEOLD.md specs/OVERVIEW.md` passed after slice 18.4 and confirmed the boundary wording is aligned across the top-level docs/spec surface.
- `rg -n "Search, source, category, and good-news filters|Search, source, and good-news filters" specs/OVERVIEW.md specs/FRONTEND.md src/frontend/app/page.tsx` passed after slice 18.5 and confirmed the overview spec now matches the shipped home-page filter controls.
- `source src/backend/.venv/bin/activate && python3 -m unittest src.backend.tests.test_refresh_processing -v` passed again after slice 18.6 added retry-exhaustion and fail-fast category-fetch regression coverage.
- `source src/backend/.venv/bin/activate && python3 -m unittest src.backend.tests.test_api_smoke -v` passed again after slice 18.6.
- `printenv NEWS_API_KEY` returned empty in this Codex environment.

## 2. Active phase
Phase 3D is still active, but the remaining work is now trusted-machine evidence rather than a repo-local backend gap. Keep the real-key refresh proof as the next slice, and do not recreate removed v1 root runtime files while doing v2 work.

## 3. Ordered checklist with [ ] and [x]
- [x] 18.1 Decide the `GET /api/articles/{id}` contract and enforce it. The detail endpoint now matches the collection endpoints and only returns `processed` rows. `specs/BACKEND.md` now documents that contract, and `src/backend/tests/test_api_smoke.py` covers `processed`, `pending`, `failed`, and missing ids.
- [x] 18.2 Add deterministic Playwright coverage for the refresh path. `src/frontend/tests/e2e/refresh-path.spec.ts` now covers accepted refresh, invalid-key feedback, duplicate-refresh attach behavior, refresh-status polling, and the 120-second timeout message using mocked frontend API responses and Playwright clock control instead of a real NewsAPI key.
- [x] 18.3 Make the local Playwright path obvious and safer. `src/frontend/package.json` now exposes `npm run test:e2e` and `npm run test:e2e:reuse`, `README.md` and `src/frontend/README.md` now explain the fixed-port ownership rule, and `specs/FRONTEND.md` now documents the current e2e entrypoints and coverage.
- [x] 18.4 Align docs with the real v2 and legacy boundary. `AGENTS.md`, `README.md`, `READMEOLD.md`, and `specs/OVERVIEW.md` now say the root-level legacy runtime files were removed on 2026-03-10 and point readers to git history or archived legacy docs instead of the checked-out repo tree.
- [x] 18.5 Resolve the frontend filter-scope mismatch. `specs/OVERVIEW.md` now matches the shipped home page and only describes the exposed search, source, and good-news controls; category filtering remains an API capability rather than a current frontend control.
- [x] 18.6 Add backend tests that prove the current fetch behavior. `src/backend/tests/test_refresh_processing.py` now covers retry exhaustion for `429`, retry exhaustion for transport errors, later-category fetch failure after an earlier category succeeds, and the current fail-fast-before-insert behavior by proving the DB stays empty when `fetch_all_categories()` aborts.
- [ ] 18.7 On a trusted local machine with a real `NEWS_API_KEY`, run the manual Phase 3 refresh evidence flow and paste the exact observed outcomes into this file. Use `python -m src.backend.scripts.seed_manual_integration_data` if cached browse needs seed data, then run `python -m src.backend.scripts.capture_manual_integration_evidence --api-key "$NEWS_API_KEY" --output <report-path>`, then complete the frontend follow-up section from `http://localhost:3000`. This remains blocked in Codex until a real key is available.
- [x] 17.x Re-verified the main v2 runtime rules in code: request-scoped NewsAPI key handling, cached browse without a key, structured refresh errors, duplicate-refresh attach logic, single-call AI analysis, and per-process refresh tracking are all present.
- [x] 17.x Re-verified the current frontend browse contract in code: the home page syncs search, source, and good-news state with the URL, the inline key onboarding remains active, and article-detail `404` and retry flows still match the current spec.
- [x] 17.x Re-ran the targeted validation set on 2026-03-11 for backend smoke, refresh-processing regressions, manual-evidence helper tests, frontend lint, and frontend typecheck.
- [x] 17.x Re-ran the current Playwright baseline on 2026-03-11 and confirmed the failure is still harness startup, not test assertions: the config could not claim `127.0.0.1:8000` because local ports `3000` and `8000` were already occupied.

## 4. Notes / discoveries that matter for the next loop
- Recent history matters. `495e6a6`, `292455c`, and `16ee745` already aligned part of the docs/spec surface and the article-detail retry flow, so the items above are the gaps that remain after those commits.
- The checked-out repo root no longer contains the old runtime files named in legacy docs. A repo search found no `batch_processor.py`, `run.py`, `search.py`, or `web_app.py` in the working tree. Do not recreate them during Phase 3 work.
- `AGENTS.md`, `README.md`, `READMEOLD.md`, and `specs/OVERVIEW.md` now consistently describe the legacy boundary: the root-level v1 runtime files were removed on 2026-03-10, and git history or archived legacy docs are the reference path for older implementation details.
- `src/frontend/package.json` now exposes the safe Playwright entrypoints directly: `npm run test:e2e` for the repo-managed fixed-port harness and `npm run test:e2e:reuse` for attaching to an already-running local app on `http://127.0.0.1:3000`.
- `src/frontend/tests/e2e/refresh-path.spec.ts` is now the repo-owned browser contract for refresh UX. It mocks `/api/refresh`, `/api/refresh/status`, `/api/articles`, `/api/sources`, and `/api/stats`, seeds a saved key through `localStorage`, and uses `page.clock` to cover the 120-second timeout path deterministically.
- `specs/OVERVIEW.md` now matches `specs/FRONTEND.md` and `src/frontend/app/page.tsx`: the shipped home page exposes search, source, and good-news controls, while `category` remains an API-level query parameter without a current frontend control.
- `src/frontend/lib/api.ts` and `src/backend/routers/articles.py` still support a `category` query param on the list endpoint. The filter exists at the API layer even though the current home page does not expose it.
- Slice 18.1 tightened `src/backend/routers/articles.py` detail reads to `processed` rows only. `src/backend/tests/test_api_smoke.py` now proves that `processed` rows are still visible while `pending` and `failed` rows return the same `404` as a missing id.
- `specs/AI_PROMPTS.md` and `src/backend/services/ai_service.py` still align on the single-call JSON analysis contract for sentiment, rewrite decision/output, TLDR, and good-news classification.
- `src/backend/tests/test_refresh_processing.py` now proves the current fetcher behavior for repeated `429` responses, repeated transport failures, and a later category failure after an earlier category succeeded.
- `src/backend/services/article_processor.py` still calls `fetch_all_categories()` before inserting any rows. Slice 18.6 added a DB-backed regression test that confirms the current fail-fast-before-insert behavior, so treat that order as the current contract unless a later plan item changes it deliberately.
- `src/frontend/playwright.config.mts` deletes its local e2e database, seeds deterministic data, and then starts backend and frontend servers on fixed local ports. Clean ports still matter before treating a Playwright startup failure as app behavior.
- This sandbox now shows two separate frontend-browser validation limits: binding a fresh local Next dev port returned `listen EPERM`, and launching Playwright Chromium failed with `bootstrap_check_in ... Permission denied (1100)`.
- During this run, `lsof -nP -iTCP:3000,8000 -sTCP:LISTEN` showed Python already listening on `127.0.0.1:8000` and `node` already listening on `3000`. That fully explains the Playwright startup failure seen on 2026-03-11.
- This Codex environment still does not expose `NEWS_API_KEY`, so real-key refresh proof remains outside the sandbox.
- In this shell, `python3` worked for backend validation. Do not assume plain `python` is on `PATH` before the virtual environment is activated.
- This Codex sandbox cannot write inside `.git/`. `git add` failed again on 2026-03-11 with `fatal: Unable to create '/Users/tombutler/Repos/NewsPerspective/.git/index.lock': Operation not permitted`. The latest completed slice cannot be staged or committed here and must be committed outside this sandbox.

## 5. Next recommended build slice
- Take 18.7 next. It is now the highest-priority unchecked item, and it needs a trusted local machine because this Codex environment still lacks `NEWS_API_KEY` and browser permissions.
- Keep trusted-machine browser execution of `src/frontend/tests/e2e/refresh-path.spec.ts` in that same follow-up so the documented Playwright entrypoints can be exercised outside this sandbox once a real local app stack is available.
