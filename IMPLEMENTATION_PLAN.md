# IMPLEMENTATION_PLAN.md

## 1. Current status summary and code review
- Updated on 2026-03-12 after the backend UTC timestamp build slice and validation rerun.
- Priority levels used below:
  - `P1`: user-visible correctness or contract bugs that should be fixed before cleanup.
  - `P2`: important regression coverage or source-of-truth alignment that depends on the `P1` fixes.
  - `P3`: developer-experience cleanup, lower-risk review follow-up, or non-blocking polish.
- GitHub / review state verified on 2026-03-12:
  - `gh issue list --state open -L 20 --json number,title,state,url` returned `[]`.
  - `gh pr status` shows PR `#3 V2.0` on branch `v2.0` with checks passing.
  - `gh pr view 3 --comments` is still mostly stale CodeRabbit history. The live findings worth carrying forward are the missing exception chaining in `src/backend/routers/sources.py`, the backend shared-process unittest isolation failure, the `ResourceWarning` from `test_api_smoke`, and the lower-severity refresh toast count/wording mismatch in `src/frontend/app/page.tsx`.
- Validation rerun during this planning pass:
  - `source src/backend/.venv/bin/activate && python -m unittest src.backend.tests.test_manual_integration_evidence -v` passed (`14` tests).
  - `source src/backend/.venv/bin/activate && python -m unittest src.backend.tests.test_api_smoke -v` passed (`25` tests) but still emitted a `ResourceWarning` about an unclosed SQLite connection at interpreter shutdown.
  - `source src/backend/.venv/bin/activate && python -m unittest src.backend.tests.test_refresh_processing -v` passed (`9` tests).
  - `source src/backend/.venv/bin/activate && python -m unittest src.backend.tests.test_api_smoke src.backend.tests.test_refresh_processing -v` still fails when both modules run in one Python process. `test_refresh_processing` hits `sqlite3.OperationalError: attempt to write a readonly database` because both modules bind different temp `DATABASE_URL` values at import time against shared engine/session state.
  - `cd src/frontend && npm run lint` passed.
  - `cd src/frontend && npm run typecheck` passed.
  - `cd src/frontend && npx playwright test tests/e2e/cached-browse.spec.ts -g "keeps the newest search results when an older article response finishes later"` passed on 2026-03-12.
  - `cd src/frontend && npx playwright test tests/e2e/refresh-path.spec.ts -g "shows a non-fatal timeout toast when polling stays in processing past 120 seconds"` passed on 2026-03-12 after the timeout reattachment fix, confirming the page still stops active polling and re-enables the refresh button after the non-fatal timeout toast.
  - `cd src/frontend && /Users/tombutler/.nvm/versions/node/v22.17.0/bin/node --test --experimental-strip-types lib/refresh-status.test.mjs` passed on 2026-03-12 after the timeout reattachment fix. Node emitted the expected experimental type-stripping warning and a `MODULE_TYPELESS_PACKAGE_JSON` warning for direct `.ts` helper loading, but all assertions passed.
  - `source src/backend/.venv/bin/activate && python -m unittest src.backend.tests.test_api_smoke -v` passed on 2026-03-12 after the UTC timestamp fix, including new coverage for timezone-aware article and stats payloads after SQLite round-trips. The existing `ResourceWarning` about an unclosed SQLite connection still appears at interpreter shutdown.
  - `source src/backend/.venv/bin/activate && python -m unittest src.backend.tests.test_refresh_processing -v` passed on 2026-03-12 after the UTC timestamp fix, confirming refresh ingestion still persists parsed NewsAPI timestamps without regression.
- Verified implementation status in current code and repo state:
  - Phase 3 trusted-machine evidence is present at `logs/phase3_manual_integration_report.md`, and the helper/report tests are green.
  - Cached read-only browse without a NewsAPI key still works by contract; refresh still requires the user key via `X-News-Api-Key`.
  - Duplicate refresh requests still short-circuit correctly and the frontend still attaches to the in-flight refresh on the normal path.
  - Homepage article loads now ignore stale responses from older search/source/good-news requests, with targeted Playwright coverage for the delayed-response race.
  - The single OpenAI call per article contract is still intact in `src/backend/services/article_processor.py`.
  - Persisted `published_at`, `fetched_at`, and `stats.latest_fetch` now round-trip through SQLite with explicit UTC timezone semantics in API responses instead of naive timestamps.
  - Good News exclusions for `sports`, `entertainment`, and detected `politics` remain implemented in backend filtering/persistence, API serialization, stats, tests, and frontend copy.
  - The persistent refresh-status card remains shipped and still combines volatile `/api/refresh/status` state with durable `/api/stats.latest_fetch`.
  - Root-level v1 runtime files remain absent; legacy reference still lives in `READMEOLD.md` and git history only.
- Review-confirmed and source-confirmed open gaps:
  - `src/backend/routers/sources.py` still re-raises refresh-validation failures without explicit exception chaining.
  - `specs/ROADMAP.md` still lists an outdated near-term loop order that points back to already-completed refresh-status and Good News slices.
  - `specs/FRONTEND.md` still needs to be updated now that same-refresh reattachment after timeout is covered by regression tests.

## 2. Active phase
Phase 4 correctness and contract hardening. The stale homepage article-response race, refresh timeout reattachment regression, and backend UTC timestamp round-trip contract are now closed. Next finish the remaining doc alignment, router review cleanup, backend test-harness isolation, and the lingering smoke-test `ResourceWarning`.

## 3. Ordered checklist with [ ] and [x]
- [x] [P1] Re-read `AGENTS.md`, `IMPLEMENTATION_PLAN.md`, `README.md`, active specs, current PR review comments, and the relevant backend/frontend source before rewriting the plan.
- [x] [P1] Reconfirm that Phase 3 trusted-machine evidence is present at `logs/phase3_manual_integration_report.md` and that the helper/report regression tests still pass.
- [x] [P1] Reconfirm the shipped v2 boundary: cached read-only browse still works without a NewsAPI key, refresh still requires `X-News-Api-Key`, the single-call AI contract is still intact, and deleted root-level v1 runtime files have not reappeared.
- [x] [P1] Re-run the smallest meaningful baseline checks on 2026-03-12: backend smoke, refresh-processing regressions, manual-evidence tests, frontend lint, and frontend typecheck all pass when run as separate commands.
- [x] [P2] Reconfirm that the persistent refresh-status UI and current Good News exclusions remain implemented and should stay closed unless new regression evidence appears.
- [x] [P1] In `src/frontend/app/page.tsx`, guard article loads against stale responses so only the newest request for the active search/source/good-news state can update feed contents, pagination, and `hasMore`.
- [x] [P1] Add the smallest meaningful frontend regression coverage proving that older article responses cannot overwrite newer filter/search state.
- [x] [P1] In `src/frontend/app/page.tsx`, clear `lastObservedProcessingKeyRef` when `waitForRefreshCompletion()` times out so the page can reattach to the same in-flight refresh later.
- [x] [P1] Add focused frontend regression coverage proving the same refresh can be re-observed after a timeout when `/api/refresh/status` still reports the same `started_at`.
- [x] [P1] Preserve explicit UTC semantics for persisted and serialized article/stats timestamps so `published_at`, `fetched_at`, and `stats.latest_fetch` emit UTC-offset datetimes after SQLite round-trips instead of naive values.
- [x] [P1] Add backend/API regression coverage proving article responses and `stats.latest_fetch` retain UTC offset semantics after SQLite persistence.
- [ ] [P2] Update `specs/FRONTEND.md` after the timeout reattachment fix so it distinguishes the already-covered timeout toast path from the new same-refresh reattachment proof.
- [ ] [P2] Update `specs/ROADMAP.md` so its near-term loop order matches the real next-build priority instead of pointing back to already-completed slices.
- [ ] [P3] Make refresh-validation exception chaining explicit in `src/backend/routers/sources.py` (`from exc` or `from None`) so the last live backend router review finding is closed cleanly.
- [ ] [P3] Align refresh-completion toast copy in `src/frontend/app/page.tsx` so the displayed count matches `new_articles` versus `processed_articles` semantics.
- [ ] [P3] Fix backend test-harness isolation so `src.backend.tests.test_api_smoke` and `src.backend.tests.test_refresh_processing` can run together in one `python -m unittest ...` invocation without colliding over module-level `DATABASE_URL`, temp DB teardown, or shared SQLAlchemy engine state.
- [ ] [P3] Resolve or intentionally document the unclosed SQLite connection warning emitted by `python -m unittest src.backend.tests.test_api_smoke -v`.

## 4. Notes / discoveries that matter for the next loop
- `logs/phase3_manual_integration_report.md` is the canonical repo-local artifact for trusted-machine Phase 3 evidence. Do not reopen a generic “manual refresh validation still pending” blocker unless a newer trusted-machine run contradicts that artifact.
- The stale-response bug is frontend-only state management. The existing `/api/articles`, `/api/refresh/status`, and `/api/stats` contract is sufficient; do not add backend endpoints for this fix.
- Existing Playwright coverage already proves cached browse, URL/back-forward control sync, accepted refresh, invalid key handling, duplicate-refresh attach, persistent refresh-status UI, restart-to-idle fallback, and the non-fatal 120-second timeout toast path.
- The stale-response regression is now covered by Playwright with a delayed older search response followed by a faster newer search response. Keep future homepage loading changes compatible with that request-order guarantee.
- The timeout reattachment fix now clears the observed processing key on timeout, and `src/frontend/lib/refresh-status.test.mjs` covers resuming the same `started_at` after that timeout-state reset.
- Backend persistence now uses an explicit UTC-normalizing datetime type for `published_at` and `fetched_at`, so SQLite-backed article payloads and `stats.latest_fetch` serialize with timezone-aware UTC values (`Z` in current FastAPI output).
- Hidden dependency for refresh-state UX: `/api/refresh/status` is volatile per-process memory, while `/api/stats.latest_fetch` is durable SQLite history. The frontend should keep treating them as different signals rather than trying to reconstruct refresh status from stats alone.
- Running `test_api_smoke` and `test_refresh_processing` together in one unittest process is still unsafe today. The reproduced failure mode on 2026-03-12 was `sqlite3.OperationalError: attempt to write a readonly database`, not just flaky ordering.
- `python -m unittest src.backend.tests.test_api_smoke -v` still emits a `ResourceWarning` about an unclosed SQLite connection even though all assertions pass. Keep that as separate cleanup work, not a reason to delay the `P1` correctness fixes.
- Current code/spec mismatch to carry explicitly: `specs/ROADMAP.md` near-term loop order is stale. Treat `IMPLEMENTATION_PLAN.md` as authoritative for execution order until that roadmap section is updated.
- Keep legacy handling conservative. If a future slice needs v1 behavior for reference, use `READMEOLD.md` or git history instead of recreating deleted root-level runtime files.

## 5. Next recommended build slice
Take the next documentation-alignment slice:

1. Update `specs/FRONTEND.md` so it reflects that the timeout path now includes same-refresh reattachment coverage.
2. Update `specs/ROADMAP.md` so its near-term loop order matches the real remaining priorities instead of pointing back to already-completed slices.
3. After the docs are aligned, take the backend cleanup slice for explicit refresh-validation exception chaining in `src/backend/routers/sources.py`.
