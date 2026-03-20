# IMPLEMENTATION_PLAN.md

## 1. Current status summary and code review
- Updated on 2026-03-20 after reading repo rules, active specs, `README.md` for context, recent local history, and the main backend/frontend runtime files.
- No new `P1` correctness regression is proven by the current local evidence.
- Verified runtime state:
  - `POST /api/refresh` still requires a user-supplied `X-News-Api-Key`. The backend still does not read a server-side `NEWS_API_KEY`.
  - Cached read-only endpoints still work without a key.
  - `src/backend/services/article_processor.py` still does one AI call per new article and stores sentiment, rewrite output, TLDR, and Good News state together.
  - Good News exclusions for `sports`, `entertainment`, and detected `politics` are still enforced in backend logic and reflected in frontend behavior.
  - Refresh timeout resume behavior is still implemented in `src/frontend/app/page.tsx` and helper-covered in `src/frontend/lib/refresh-status.test.mjs`.
  - The visible-headline fallback lives in `src/frontend/lib/headlines.ts`, not `src/frontend/lib/utils.ts`.
  - Root-level v1 runtime files remain absent. Legacy reference still lives in `READMEOLD.md` and git history only.
- Validation snapshot on 2026-03-20:
  - `source src/backend/.venv/bin/activate && python -m unittest src.backend.tests.test_api_smoke src.backend.tests.test_refresh_processing src.backend.tests.test_manual_integration_evidence -v` passed (`52` tests).
  - `cd src/frontend && npm run lint` passed.
  - `cd src/frontend && npm run typecheck` passed.
  - `cd src/frontend && node --test --experimental-strip-types lib/headlines.test.mjs lib/refresh-status.test.mjs` passed (`7` tests) with the expected experimental warnings.
  - `cd src/frontend && npm run test:e2e` did not reach browser assertions in this sandbox because the managed backend process could not bind `127.0.0.1:8000` (`operation not permitted`). Treat that as environment behavior, not a proven app regression.
- Open review findings to carry forward:
  - [P2] `specs/ROADMAP.md` is stale. Its `Near-Term Loop Order` still points at already-finished backend review cleanup.
  - [P2] `specs/FRONTEND.md` is stale in more than one place. Its `Current Project Structure` omits shipped files such as `components/refresh-status-card.tsx`, `components/toaster.tsx`, `lib/headlines.ts`, `lib/refresh-status.ts`, and the focused helper tests.
  - [P3] The noisy `nvm` help banner appears before frontend `npm` commands in this shell, but repo search found only `.nvmrc` and README mentions. Treat it as local shell/environment behavior unless a future loop reproduces it from repo-managed scripts.
- Review-state limits:
  - Local git history after the old 2026-03-12 plan shows fresh commits for roadmap text, router exception chaining, frontend headline helper extraction, and focused helper tests.
  - Live GitHub issue and PR comment state is still unverified in this sandbox on 2026-03-20 because `gh issue list`, `gh pr status`, and `gh pr view --comments` failed with `error connecting to api.github.com`.
- Top-level docs check:
  - `README.md` and `src/frontend/README.md` are broadly aligned with the current runtime. The active drift in this pass is mainly in `specs/ROADMAP.md` and `specs/FRONTEND.md`.

## 2. Active phase
Phase 5 is documentation alignment and validation boundaries.

The earlier correctness fixes still appear to be in place. The next safe loop should stop reopening completed backend/frontend regression work and instead repair the stale active specs. Keep the difference clear between seeded automated coverage, trusted-machine real-key evidence, and sandbox-only limits.

## 3. Ordered checklist with [ ] and [x]
- [x] [P1] Re-read `AGENTS.md`, the old `IMPLEMENTATION_PLAN.md`, `README.md`, the active specs, and trusted-machine evidence before rewriting the plan.
- [x] [P1] Inspect enough backend/frontend source to verify the refresh contract, cached read-only contract, Good News exclusions, visible-headline helper path, and refresh timeout resume behavior.
- [x] [P1] Re-run a focused validation snapshot: combined backend suites, frontend lint/typecheck, focused frontend helper tests, and a managed Playwright attempt.
- [x] [P2] Review `README.md` and `src/frontend/README.md` against the runtime and active specs. No higher-priority blocker was found there.
- [x] [P3] Check whether the noisy `nvm` banner is repo-managed. Current evidence says no: repo search found only `.nvmrc` and doc mentions.
- [ ] [P2] Update `specs/ROADMAP.md` so `Near-Term Loop Order` stops pointing at the already-finished router exception-chaining cleanup and instead points at the real next doc-alignment work.
- [ ] [P2] Update `specs/FRONTEND.md` so `Current Project Structure` lists the shipped helper/status files and the visible-headline helper path is explicit.
- [ ] [P2] After the spec edits land, run `git diff --check -- specs/ROADMAP.md specs/FRONTEND.md IMPLEMENTATION_PLAN.md` plus frontend lint/typecheck and the focused frontend helper tests.
- [ ] [P3] Rerun Playwright on a machine that can bind `127.0.0.1:8000` and `127.0.0.1:3000`, or use `npm run test:e2e:reuse` against an already-running local stack when validating the trusted-machine flow.
- [ ] [P3] Keep the legacy boundary explicit during doc cleanup. If a future slice needs v1 reference behavior, use `READMEOLD.md` or git history instead of recreating deleted root-level runtime files.

## 4. Notes / discoveries that matter for the next loop
- `logs/phase3_manual_integration_report.md` is still present and still matches the v2 boundary at a high level. Refresh it only if the refresh contract or visible refresh UI copy changes.
- The manual evidence helper intentionally leaves human-fill `TODO` placeholders in generated report sections. That is part of the workflow, not a broken implementation.
- `specs/FRONTEND.md` project structure is more stale than the old plan said. It misses `components/refresh-status-card.tsx`, `components/toaster.tsx`, `lib/headlines.ts`, `lib/refresh-status.ts`, `lib/headlines.test.mjs`, and `lib/refresh-status.test.mjs`.
- `npm run test:e2e` currently needs a machine that can open the managed backend/frontend ports. In this Codex sandbox it failed before assertions because binding `127.0.0.1:8000` was not permitted.
- The frontend helper tests currently rely on `node --test --experimental-strip-types`. The experimental warnings are expected in the current setup and are not new regressions.
- The noisy `nvm` help banner does not appear to come from repo-managed scripts. It most likely comes from the login-shell environment used in this Codex session.
- The `gh` CLI could not reach GitHub from this environment on 2026-03-20, so do not claim live issue/review state is current unless a future loop reruns those commands with network access.
- The recent local commit history is newer than the old plan. Treat the old 2026-03-12 planning text as historical context only, not as the current source of truth.

## 5. Next recommended build slice
Update `specs/ROADMAP.md` first.

That is the smallest high-value slice because the roadmap still tells the next build loop to work on a backend cleanup that is already complete. Keep that slice doc-only. Validate it with `git diff --check`. After that lands, take a second small doc-only slice for the broader `specs/FRONTEND.md` structure and helper-path alignment.
