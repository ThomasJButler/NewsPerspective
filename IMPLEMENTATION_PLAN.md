# IMPLEMENTATION_PLAN.md

## 1. Current status summary and code review
- Updated on 2026-03-12 after the roadmap-spec cleanup slice across `IMPLEMENTATION_PLAN.md` and `specs/ROADMAP.md`.
- Priority guide:
  - `P1`: correctness or validation regressions that block safe build work.
  - `P2`: shipped-behavior or source-of-truth alignment that should land after `P1`.
  - `P3`: smaller cleanup or remaining review follow-up once higher-risk items are closed.
- GitHub / review state verified on 2026-03-12:
  - `gh issue list --state open -L 20 --json number,title,state,url` returned `[]`.
  - `gh pr status` shows PR `#3 V2.0` on branch `v2.0` with checks passing.
  - `gh pr view 3 --comments` is still mostly stale CodeRabbit history.
  - The only still-live router review item confirmed in code is missing explicit exception chaining in `src/backend/routers/sources.py`.
  - Earlier review items already reflected in current code/specs include the SQLAlchemy boolean cleanup, the `curl --config -` refresh example in `README.md`, the `text` fence in `specs/OVERVIEW.md`, and the aggregated source/stats helpers in `src/frontend/tests/e2e/refresh-path.spec.ts`.
- Validation snapshot from 2026-03-12:
  - `source src/backend/.venv/bin/activate && python -m unittest src.backend.tests.test_api_smoke -v` passed (`27` tests) with no SQLite `ResourceWarning` after the lifecycle fix.
  - `source src/backend/.venv/bin/activate && python -m unittest src.backend.tests.test_refresh_processing -v` passed (`9` tests).
  - `source src/backend/.venv/bin/activate && python -m unittest src.backend.tests.test_api_smoke src.backend.tests.test_refresh_processing -v` passed (`36` tests) in one Python process after rebinding/disposal of the shared SQLAlchemy engine between suites.
  - `source src/backend/.venv/bin/activate && python -m unittest src.backend.tests.test_manual_integration_evidence -v` passed (`14` tests).
  - `cd src/frontend && npm run lint` passed.
  - `cd src/frontend && npm run typecheck` passed.
  - `cd src/frontend && npm run test:e2e:reuse -- tests/e2e/refresh-path.spec.ts --grep "completes an accepted refresh and reloads cached data after polling"` passed against the already-running local app stack on `127.0.0.1:3000` / `127.0.0.1:8000`.
  - `cd src/frontend && /Users/tombutler/.nvm/versions/node/v22.17.0/bin/node --test --experimental-strip-types lib/refresh-status.test.mjs` passed, with the expected experimental type-stripping and `MODULE_TYPELESS_PACKAGE_JSON` warnings.
  - `git diff --check -- specs/FRONTEND.md IMPLEMENTATION_PLAN.md` passed for this doc slice.
- Verified implementation status in current code:
  - `logs/phase3_manual_integration_report.md` is present and records trusted-machine refresh evidence captured on 2026-03-12.
  - Cached browse without a saved NewsAPI key still works by contract; refresh still requires `X-News-Api-Key`.
  - The single OpenAI call per article contract remains intact in `src/backend/services/article_processor.py`.
  - Resume-after-timeout handling for the same in-flight refresh is implemented in `src/frontend/app/page.tsx` and unit-covered in `src/frontend/lib/refresh-status.test.mjs`.
  - Root-level v1 runtime files remain absent; legacy reference stays in `READMEOLD.md` and git history.
- Confirmed mismatches and remaining follow-up:
  - The only live follow-up still tracked from router review is explicit exception chaining in `src/backend/routers/sources.py`.

## 2. Active phase
Phase 4 closeout: the backend validation-isolation and SQLite lifecycle warnings are closed, the refresh completion toast now distinguishes added-new count from processed count, `specs/FRONTEND.md` documents timeout-reset / same-refresh resume behavior, and `specs/ROADMAP.md` no longer points the near-term order at completed frontend slices. The next loop should take the remaining router review cleanup. Phase 3 trusted-machine evidence is current, and no new runtime contract break was found in the app flow.

## 3. Ordered checklist with [ ] and [x]
- [x] [P1] Re-read `AGENTS.md`, `IMPLEMENTATION_PLAN.md`, `README.md`, active specs, trusted-machine evidence, and relevant backend/frontend source before rewriting this plan.
- [x] [P1] Reconfirm that Phase 3 evidence is still present at `logs/phase3_manual_integration_report.md` and still matches the current v2 boundary.
- [x] [P1] Re-run the focused validation snapshot on 2026-03-12: backend suites individually, the combined backend invocation, manual integration evidence tests, frontend lint/typecheck, and `lib/refresh-status.test.mjs`.
- [x] [P1] Fix backend test-harness isolation so `python -m unittest src.backend.tests.test_api_smoke src.backend.tests.test_refresh_processing -v` passes in one Python process.
- [x] [P1] Eliminate or intentionally explain the unclosed SQLite `ResourceWarning` emitted by `python -m unittest src.backend.tests.test_api_smoke -v`, then revalidate that suite.
- [x] [P2] Align refresh completion toast copy in `src/frontend/app/page.tsx` so it does not label `processed_articles` as `new articles`; update focused frontend coverage if the observable text changes.
- [x] [P2] Update `specs/FRONTEND.md` so the Refresh UX section documents the shipped timeout-reset / same-refresh resume behavior after a 120-second polling timeout.
- [x] [P2] Update `specs/ROADMAP.md` so its near-term loop order matches the actual remaining priorities instead of already-finished slices.
- [ ] [P3] Make refresh-validation exception chaining explicit in `src/backend/routers/sources.py` (`from exc` or `from None`) so the last live router review finding is closed cleanly.

## 4. Notes / discoveries that matter for the next loop
- `src.backend.database` now exposes explicit engine lifecycle hooks for tests: `reconfigure_engine(database_url)` rebinds `engine` and `SessionLocal`, and `dispose_engine()` closes the current SQLite connection cleanly.
- The combined-suite failure was deterministic, not flaky. `src.backend.tests.test_api_smoke` imports `src.backend.database` first, so `src.backend.tests.test_refresh_processing` must explicitly rebind that shared module to its own temp database before calling `create_all(...)`.
- The smoke-suite `ResourceWarning` disappeared once the smoke path stopped creating a second same-path engine and instead disposed the original engine in `tearDownClass()`.
- `README.md` and `src/frontend/README.md` are close to the shipped runtime. The main documentation gaps for this pass are in the active specs rather than the top-level docs.
- The refresh success toast in `src/frontend/app/page.tsx` now uses `new_articles` for “Added X new articles.” and the focused refresh e2e path keeps `new_articles` and `processed_articles` different so that regression is covered.
- `specs/FRONTEND.md` now describes the shipped timeout-reset / same-refresh resume behavior, and `specs/ROADMAP.md` now points the near-term order at the actual remaining cleanup instead of completed refresh-status / Good News slices.
- If a future slice changes refresh request/status behavior or user-visible refresh copy, refresh the trusted-machine evidence so `logs/phase3_manual_integration_report.md` does not drift.
- Keep the legacy boundary strict. If a future slice needs v1 reference behavior, use `READMEOLD.md` or git history instead of recreating deleted root-level runtime files.

## 5. Next recommended build slice
Take the router review cleanup slice:

1. Update `src/backend/routers/sources.py` so refresh-validation exceptions use explicit chaining (`from exc` or `from None`) and the last live router review finding is resolved.
2. Run the smallest backend validation that exercises the refresh router path after that edit.
3. Update this plan to mark the router cleanup complete and confirm whether any review-driven follow-up still remains.
