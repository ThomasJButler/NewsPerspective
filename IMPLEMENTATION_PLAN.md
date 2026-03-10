# IMPLEMENTATION_PLAN.md

## Current status summary and code review
- Re-checked on 2026-03-10 in plan/build mode. Read `AGENTS.md`, `IMPLEMENTATION_PLAN.md`, `README.md`, `READMEOLD.md`, all files in `specs/`, recent commits, and the active backend/frontend/legacy source that drives refresh, browsing, filtering, stats, detail pages, and the v1 boundary.
- The active v2 runtime is still `src/backend/` plus `src/frontend/`. Root-level files remain legacy/reference-only unless a later cleanup slice explicitly targets them.
- No repo-local issue tracker entries or written code review notes were found.
- Recent commits still show the current sequence of app work:
  - `cc8a629` Use US headlines as the default NewsAPI country
  - `738bcac` Fix Next.js config.
  - `77304eb` Add backend seed and test package files
  - `3bf9a15` Polish frontend local state and tooling
  - `6940e61` Remove unused legacy root files
  - `ff36199` Improve Ralph loop guidance and learning modes
- Current worktree state matters for the next loop:
  - `README.md`
  - `loop.sh`
  - `batch_processor.py` is still deleted locally
  - `.nvmrc`
  - `src/frontend/package.json`
  - `src/frontend/package-lock.json`
  - `src/frontend/next.config.ts`
  - The backend normalized-source plus refresh-smoke slice is no longer part of the dirty worktree boundary once this loop's narrow commit is created.
  - The frontend files remain a separate Step 17.1 DX slice: repo-owned Node pinning, a `typecheck` script, and an explicit Turbopack repo root.
- Fresh validation on 2026-03-10:
  - `source src/backend/.venv/bin/activate && python -m unittest src.backend.tests.test_api_smoke -v` passed all 14 tests.
  - `source src/backend/.venv/bin/activate && python -m unittest src.backend.tests.test_manual_integration_evidence -v` passed all 5 tests.
  - `source src/backend/.venv/bin/activate && python -m src.backend.scripts.capture_manual_integration_evidence --output /tmp/phase3_manual_integration_report.md` completed successfully and wrote a Markdown report that classified the no-server run as environment behavior/still unproven, which matches the helper contract.
  - `touch .git/codex-write-test && rm .git/codex-write-test` succeeded in this environment, so the earlier `.git` write blocker did not apply to this loop.
  - Narrow staging and commit of the backend slice succeeded after the smoke pass.
  - `npm run lint` passed in `src/frontend/`.
  - `npm run typecheck` passed in `src/frontend/`.
  - `cd src/frontend && npx playwright test tests/e2e/cached-browse.spec.ts --project=chromium` passed 2 browser tests against a seeded local backend/frontend stack.
  - `node -v` in `src/frontend/` reported `v22.17.0`.
  - `npm run build` in `src/frontend/` still failed in this Codex sandbox because Turbopack hit `Operation not permitted` while creating a CSS worker process and binding to a port.
  - After setting `turbopack.root` to the repo root in `src/frontend/next.config.ts`, the old parent-lockfile workspace-root warning did not appear before that same sandbox-specific Turbopack panic.
- Verified current code behavior:
  - `POST /api/refresh` requires `X-News-Api-Key`, validates it against NewsAPI with a 5-second timeout, returns typed error payloads, and only then queues background processing.
  - `GET /api/refresh/status` exists and exposes in-memory refresh state from `src/backend/services/refresh_tracker.py`.
  - Duplicate refresh attempts still short-circuit before NewsAPI validation.
  - Read-only endpoints still work without a NewsAPI key by serving cached processed rows.
  - NewsAPI fetching now uses `/v2/top-headlines` only and defaults to `country=us`.
  - The backend read contract now makes `GET /api/articles`, `GET /api/articles/{id}`, `GET /api/sources`, and `GET /api/stats` agree on trimmed/fallback source labels instead of leaking raw blanks.
  - The home page still keeps cached browsing available without a saved key and shows the inline `ApiKeySetup` card instead of fullscreen onboarding.
  - The frontend still polls `/api/refresh/status` for up to 120 seconds and treats that timeout as "still running" rather than a hard failure.
- Current code review findings, highest risk first:
  - [P1] Phase 3 manual integration evidence is still missing from a trusted local run and cannot be fully gathered inside this Codex sandbox because it requires local servers, outbound NewsAPI access, and a real user key.
  - [P2] The repo now has initial Playwright config and seeded cached-browse coverage, but there is still no repo-owned npm script and no refresh-path browser coverage yet.
  - [P2] Docs and specs still drift from the running v2 app:
    - `README.md` is still Ralph-loop-first instead of app-first.
    - `src/frontend/README.md` is still stock Next.js text.
    - `READMEOLD.md` still contains live v2 backend setup even though it is labeled legacy.
    - `specs/OVERVIEW.md` still describes Azure OpenAI and says NewsAPI only requires `NEWS_API_KEY`.
    - `specs/BACKEND.md` still mentions `/v2/everything` and misses `/api/refresh/status`, typed refresh errors, the 5-second validation timeout, and the normalized-source read contract.
    - `specs/FRONTEND.md` still says `next.config.js`, describes fullscreen onboarding as the main first-visit flow, and does not match Next.js `16.1.6`.
  - [P3] Frontend DX cleanup is partly improved but not fully closed. The repo now has a root `.nvmrc`, frontend `engines`, `npm run typecheck`, and an explicit Turbopack root, but `npm run build` still depends on a Turbopack path that fails in this sandbox with a CSS worker port-bind panic.
  - [P3] `batch_processor.py` is still the remaining root-level legacy runtime-like file. It imports deleted modules such as `logger_config`, `azure_ai_language`, and `azure_document_intelligence`, so it is reference-only until a dedicated legacy cleanup slice decides its fate.

## Active phase
Phase 3D. The backend normalized-source and refresh-smoke slice is now landed. Continue integration hardening with environment-gated manual evidence, repo-owned browser coverage, DX cleanup, doc/spec alignment, and legacy-boundary cleanup.

## Ordered checklist
- [x] Re-read repo rules, current plan, README context, specs, recent commits, and enough backend/frontend/legacy source to verify the real v2 status.
- [x] Search for repo-local issues/code-review notes and inspect the current worktree state.
- [x] Re-run backend smoke validation with `python -m unittest src.backend.tests.test_api_smoke -v`.
- [x] Re-run frontend lint and TypeScript validation.
- [x] Re-check frontend build behavior in this environment: `npm run build` fails under sandboxed Turbopack, while `npx next build --webpack` passes.
- [x] Re-confirm the current refresh contract, refresh-status endpoint, and in-memory tracker behavior in code.
- [x] Re-confirm the current inline no-key browsing flow and frontend refresh polling/error handling.
- [x] Re-confirm there is no repo-owned Playwright config, end-to-end suite, or Node version pin file.
- [x] Re-confirm that `batch_processor.py` is still legacy-only and not part of the v2 runtime.
- [x] Step 16.4. Normalize source labels across backend read endpoints and stats.
- [x] Step 16.5. Extend backend smoke coverage for normalized source behavior.
- [x] Step 16.6. Add refresh success-path smoke coverage.
- [x] Step 16.6a. Preserve and land the already-implemented backend slice safely.
- [x] Decide whether the current dirty backend files are the slice to keep; do not start unrelated edits in those files until that decision is explicit.
- [x] Re-run `python -m unittest src.backend.tests.test_api_smoke -v` for the backend slice before staging it.
- [x] Re-check whether the earlier `.git` write blocker still applies in the current environment before attempting the landing commit.
- [x] Stage/commit only `src/backend/routers/articles.py`, `src/backend/routers/sources.py`, `src/backend/tests/test_api_smoke.py`, `src/backend/utils/source_normalization.py`, and this plan update for the slice boundary.
- [x] Resolve the current landing blocker for this loop so the backend slice is committed without mixing in unrelated worktree changes.
- [x] Review the existing Step 16.7 helper/test files against the current refresh contract before deciding whether to land them.
- [x] Step 16.7a. Land the backend-side manual integration evidence helper and unit coverage.
- [x] Add a CLI helper that captures backend-side manual integration observations into a Markdown report with frontend follow-up placeholders.
- [x] Add backend unit coverage for the helper's classification/report formatting behavior.
- [x] Run targeted validation for the helper slice with both `python -m unittest src.backend.tests.test_manual_integration_evidence -v` and a no-server CLI smoke invocation.
- [ ] Step 16.7. Gather the missing Phase 3 manual integration evidence on a trusted local machine that can run both local servers and use a real NewsAPI key.
- [ ] Seed cached data first with `python -m src.backend.scripts.seed_manual_integration_data` if browse screens need data before a real refresh.
- [ ] Record exact results for cached browse without a key, successful refresh with a real key, invalid-key handling, duplicate refresh behavior, refresh-status polling during a long refresh, and final completion state.
- [ ] Label each recorded result as code behavior, environment behavior, documentation mismatch, or still unproven.
- [ ] Step 16.8. Add repo-owned Playwright coverage for the highest-value local browser flows.
- [x] Step 16.8a. Add initial Playwright config plus seeded cached-browse coverage.
- [x] Add `src/frontend/playwright.config.mts` with isolated backend seeding, local frontend/backend webServer startup, and artifacts under `output/playwright/`.
- [x] Add a Chromium e2e spec for cached browse without a key, source filtering, search, and article detail against seeded data.
- [x] Ignore Playwright artifacts under `output/playwright/`.
- [x] Validate the browser harness with `cd src/frontend && npx playwright test tests/e2e/cached-browse.spec.ts --project=chromium`.
- [ ] Add repo-owned npm scripts for Playwright once the already-dirty frontend package-metadata slice is ready to land cleanly.
- [x] Cover seeded cached browse without a key, source filtering, search, and article detail against a real local frontend/backend pair.
- [ ] Make refresh-related browser cases opt-in and environment-gated until either real-key manual evidence exists or a supported backend test double is added.
- [x] Step 17.1. Add repo-owned frontend DX guardrails.
- [x] Add `npm run typecheck`.
- [x] Pin or document the supported Node runtime in a repo-owned file or `package.json` `engines`.
- [x] Resolve the workspace-root warning by setting `turbopack.root` to the repo root; keep the remaining Turbopack sandbox panic tracked separately.
- [ ] Step 17.2. Align top-level docs with the running v2 system.
- [ ] Rewrite the root `README.md` so the v2 app runtime and setup come first and the Ralph loop comes second.
- [ ] Replace the stock `src/frontend/README.md` with real frontend setup, proxy, and local run notes.
- [ ] Remove live v2 setup guidance from `READMEOLD.md` so it is clearly legacy-only.
- [ ] Step 17.3. Reconcile spec drift in `specs/OVERVIEW.md`, `specs/BACKEND.md`, and `specs/FRONTEND.md`.
- [ ] Document request-scoped `X-News-Api-Key` and optional `OPENAI_API_KEY`.
- [ ] Document `/api/refresh/status`, typed refresh errors, the 5-second validation timeout, the in-memory limits of the refresh tracker, and the normalized-source read contract.
- [ ] Document category-based `/v2/top-headlines` fetching only.
- [ ] Document Next.js `16.1.6`, `next.config.ts`, Tailwind v4, the current inline onboarding flow, and the current build-validation caveat.
- [ ] Step 17.4. Lock down the legacy v1 boundary safely.
- [ ] Decide whether `batch_processor.py` stays as archived reference, moves later, or is removed in a dedicated cleanup slice.
- [ ] Make docs and ignore rules match that decision.
- [ ] Do not touch root-level legacy code until the runtime, test, and docs slices above are stable.

## Notes / discoveries that matter for the next loop
- `src/backend/routers/articles.py` now serializes normalized `source_name` values through a shared helper before returning article list/detail payloads.
- `src/backend/routers/sources.py` now counts distinct normalized source labels in `/api/stats`, which matches `/api/sources`.
- `src/backend/tests/test_api_smoke.py` now covers messy source rows plus the refresh success path, and the suite passes at 14 tests.
- `src/backend/services/refresh_tracker.py` is still in-memory and per-process. That is acceptable for one local dev server but not durable across reloads, restarts, or multiple workers.
- `GET /api/articles` still returns only rows where `processing_status == "processed"`. Manual browse checks need seeded data or a successful refresh first.
- `src/backend/scripts/seed_manual_integration_data.py` provides deterministic processed rows for local manual integration checks.
- `src/backend/scripts/capture_manual_integration_evidence.py` now provides a repeatable Step 16.7 helper that probes the backend HTTP contract, classifies each scenario, and writes a Markdown report with explicit frontend manual follow-up placeholders.
- `src/frontend/next.config.ts` still rewrites `/api/:path*` to `http://localhost:8000/api/:path*`, so real frontend integration still depends on a separate backend listener on port `8000`.
- The earlier `.git` write blocker did not reproduce in this loop; direct `.git` writes succeeded and the backend slice was landed with a narrow commit.
- `src/backend/tests/test_manual_integration_evidence.py` covers the helper's empty-cache, invalid-key, duplicate-refresh, refresh-status, and report-template behavior.
- The repo now has a root `.nvmrc`, frontend `engines.node`, and `npm run typecheck`.
- `src/frontend/playwright.config.mts` now starts an isolated seeded backend plus the Next dev server and writes browser artifacts under `output/playwright/`.
- `src/frontend/tests/e2e/cached-browse.spec.ts` now covers cached browse without a key, source filtering, search, and article detail against seeded data.
- There is still no repo-owned Playwright npm script because `src/frontend/package.json` and `src/frontend/package-lock.json` already contain unrelated dirty Step 17.1 changes and were intentionally left out of this slice boundary.
- `npm run build` currently fails only on the Turbopack path in this sandbox with `Operation not permitted` while creating a CSS worker process. After setting `turbopack.root`, the misleading parent-lockfile workspace warning no longer appears before that panic.
- The biggest written mismatches are still:
  - `README.md` is loop-first instead of app-first.
  - `src/frontend/README.md` is still boilerplate.
  - `READMEOLD.md` still contains live v2 setup steps.
  - `specs/OVERVIEW.md` still describes Azure OpenAI and incorrect NewsAPI setup.
  - `specs/BACKEND.md` still describes old NewsAPI fetching and misses the refresh status/error/source-normalization contract.
  - `specs/FRONTEND.md` still describes older framework/setup details and the older onboarding story.
- `batch_processor.py` still imports deleted legacy modules and old Azure services. Treat it as legacy reference only until Step 17.4 decides its fate.

## Next recommended build slice
Step 16.7 on a trusted local machine with a real NewsAPI key remains the highest-priority remaining slice.

Run `python -m src.backend.scripts.capture_manual_integration_evidence` on a trusted local machine, seed cached data if needed, verify cached browse without a key, successful refresh with a real key, invalid-key handling, duplicate refresh behavior, refresh-status polling during a long refresh, and final completion state, then fill in the frontend follow-up notes and classify each result as code behavior, environment behavior, documentation mismatch, or still unproven. If the next loop stays in this Codex sandbox instead, continue Step 16.8 by wiring repo-owned Playwright npm scripts and then adding environment-gated refresh browser cases.
