# IMPLEMENTATION_PLAN.md

## 1. Current status summary and code review
- [P3] `src/backend/services/refresh_tracker.py` remains in-memory and per-process. That still matches the current spec and is a documented limitation, not the next implementation target.
- Updated on 2026-03-12 after fixing the current local review findings in `src/backend/routers/articles.py`, `src/backend/routers/sources.py`, `src/backend/scripts/capture_manual_integration_evidence.py`, `src/backend/tests/test_api_smoke.py`, `src/backend/tests/test_manual_integration_evidence.py`, and `src/frontend/tests/e2e/refresh-path.spec.ts`.
- Accessible GitHub state in this environment:
  - `gh issue list -L 20` previously returned no open issues.
  - The open `V2.0` PR review remains the highest-signal external review artifact for this repo.
- Current repo head is still `e2a91c6` (`Return only processed articles; add refresh e2e`). The fixes below are local worktree changes, not a new commit.
- Fresh validation rerun during this implementation pass:
  - Backend: `python3 -m unittest src.backend.tests.test_api_smoke -v` passed.
  - Backend: `python3 -m unittest src.backend.tests.test_manual_integration_evidence -v` passed.
  - Frontend: `cd src/frontend && npm run typecheck` passed.
  - Frontend: `cd src/frontend && npx playwright test tests/e2e/refresh-path.spec.ts` passed.
- Verified implementation status in code:
  - `src/backend/routers/articles.py` now orders `/api/articles` by `nulls_last(Article.published_at.desc())` and `Article.id.asc()`, and smoke coverage now proves stable pagination across tied and null `published_at` rows.
  - `src/backend/routers/sources.py` now redacts the user-supplied NewsAPI key from transport-level validation failures before returning the structured `502 upstream_transport_failure` response.
  - `src/backend/scripts/capture_manual_integration_evidence.py` now distinguishes an accepted refresh start from a duplicate `Refresh already in progress.` response, and it now treats HTTP `>=400` `/api/refresh/status` polls as backend-contract failures instead of collapsing them into "still unproven".
  - `src/frontend/tests/e2e/refresh-path.spec.ts` now uses exact-match toast locators for the refresh completion assertions, and the targeted refresh-path Playwright spec now passes locally.
  - Processed-only visibility remains enforced across article list/detail, sources, and stats surfaces, with smoke coverage for pending/failed detail `404` behavior.
  - Structured refresh validation errors, duplicate-refresh short-circuiting at the API layer, tracker-state restoration after validation failure, and background-refresh regression coverage remain in place.
- Re-verified open implementation work that still remains:
  - [P2] `src/frontend/tests/e2e/refresh-path.spec.ts` still uses simplified mock builders that do not fully mirror backend aggregation semantics, and the timeout case still asserts a polling cadence threshold instead of only user-visible outcomes.
  - [P2] `specs/BACKEND.md` still claims the retry and later-category partial-failure paths are only lightly covered even though `src/backend/tests/test_refresh_processing.py` covers them.
  - [P2] `src/frontend/README.md` still describes Playwright coverage as cached-browse only even though the suite also covers refresh-path flows.
  - [P2] `AGENTS.md` frontend validation still omits `npm run lint` and `npm run typecheck`.
  - [P2] `specs/OVERVIEW.md` still leaves the ASCII architecture block unlabeled instead of using a `text` fence.
  - [P2] Secret-handling docs and helper flow remain inconsistent. `README.md` and `AGENTS.md` still show `curl -H "X-News-Api-Key: $NEWS_API_KEY"`, while `src/frontend/README.md` and `src/backend/scripts/capture_manual_integration_evidence.py` still rely on `capture_manual_integration_evidence --api-key "$NEWS_API_KEY"`, which exposes the key via argv during local use.
  - [P3] `src/backend/tests/test_refresh_processing.py` still leaves `_DummySession` with only `close()`, not defensive stubs for other session methods.
  - [P3] `src/frontend/app/article/[id]/page.tsx` still declares and uses the redundant `articleImageLoader` while also setting `unoptimized` on `Image`.

## 2. Active phase
Phase 3D remains active. The local P1 review findings from the article API, refresh validation path, manual-evidence helper, and refresh-path Playwright slice are now closed in the worktree. The next priority is the remaining P2 refresh-path fixture/doc drift, then the repo-wide doc alignment, and only then the trusted-machine evidence pass. Keep the 2026-03-10 v2 boundary intact: if legacy v1 behavior needs reference, recover it from git history or `READMEOLD.md` instead of recreating root-level runtime files.

## 3. Ordered checklist with [ ] and [x]
- [x] [P1] Stabilize `/api/articles` pagination ordering in `src/backend/routers/articles.py`. Added the deterministic `Article.id.asc()` tiebreaker after `nulls_last(Article.published_at.desc())` and added backend regression coverage for tied and null `published_at` rows so offset pagination stays stable.
- [x] [P1] Fix `src/backend/scripts/capture_manual_integration_evidence.py:evaluate_refresh_start(...)` so duplicate `Refresh already in progress.` responses are classified as duplicate short-circuit behavior, not as successful new refresh starts. Added regression tests in `src/backend/tests/test_manual_integration_evidence.py` for both accepted-refresh and duplicate-refresh evaluation, and reused the same acceptance gate in `main()`.
- [x] [P1] Fix `src/backend/scripts/capture_manual_integration_evidence.py:evaluate_polling(...)` so HTTP `>=400` `/api/refresh/status` responses count as failures even when `_capture_response()` returned `ok=True`. Added regression tests proving those responses surface as backend-contract failures instead of "still unproven".
- [x] [P1] Redact the user-supplied NewsAPI key from refresh validation transport errors in `src/backend/routers/sources.py`. Added smoke coverage proving the structured `502` response no longer echoes the key.
- [x] [P1] Fix the refresh completion assertions in `src/frontend/tests/e2e/refresh-path.spec.ts` to use exact-match toast locators, then reran the targeted Playwright spec until the previously failing slice passed locally.
- [ ] [P2] Bring `src/frontend/tests/e2e/refresh-path.spec.ts` fixtures in line with backend behavior. Aggregate duplicate sources correctly, compute `latest_fetch` from the newest `fetched_at`, extract a shared refresh-status builder if it reduces duplication, and replace cadence-coupled assertions with outcome-based checks where possible.
- [ ] [P2] Resolve the trusted-machine key-handling contract across docs and helper flow. Decide one supported local pattern for refresh/manual-evidence commands: either extend the helper so a real key can be supplied without argv exposure, or keep the current helper contract but document the argv-exposure tradeoff explicitly as local-only. Update `README.md`, `AGENTS.md`, `src/frontend/README.md`, and the helper usage text/docstring together so they do not contradict each other.
- [ ] [P2] Align shipped docs/specs with current code: remove the stale backend coverage warning from `specs/BACKEND.md`; update `src/frontend/README.md` to mention both cached-browse and refresh-path Playwright coverage; add `npm run lint` and `npm run typecheck` to the frontend validation guidance in `AGENTS.md`; label the ASCII diagram fence in `specs/OVERVIEW.md` as `text`.
- [ ] [P3] Apply the remaining low-risk cleanup after the higher-priority items above land: add defensive stub methods to `_DummySession` in `src/backend/tests/test_refresh_processing.py`, and remove the redundant `articleImageLoader` / `loader={articleImageLoader}` pair from `src/frontend/app/article/[id]/page.tsx`.
- [ ] [P2] After the local fixes above land, finish the trusted-machine Phase 3 evidence pass on a real local machine: seed cached data first with `source src/backend/.venv/bin/activate && python -m src.backend.scripts.seed_manual_integration_data` if `/api/articles` is empty; run `python -m src.backend.scripts.capture_manual_integration_evidence` against the already running local stack using whatever key-supply pattern the previous checklist item standardizes; keep the same backend/frontend stack running and execute the exact reuse-path Playwright command printed in the generated report; open the frontend URL from the report, complete the frontend follow-up table with exact cached-browse and refresh outcomes, and paste the final observed results back into this file.
- [ ] [P3] For any documentation-only slice above, run the smallest proof set for the touched files: use targeted `rg` checks to confirm stale wording is gone; rerun `python3 -m unittest src.backend.tests.test_refresh_processing -v` if `specs/BACKEND.md` changed; rerun the smallest relevant command/example checks and `cd src/frontend && npm run test:e2e:reuse -- --list` if Playwright guidance changed.
- [x] Backend smoke, manual-evidence, frontend typecheck, and the targeted refresh-path Playwright validations currently pass in this worktree.
- [x] Repo-managed and reuse-path Playwright entrypoints already exist, and the current suite still includes both cached-browse and refresh-path coverage.
- [x] The checked-out repo still reflects the v2 boundary: root-level v1 runtime files remain removed and legacy reference is preserved through history and `READMEOLD.md`.

## 4. Notes / discoveries that matter for the next loop
- The open PR review remains the highest-signal external review artifact, but the local P1 findings around pagination stability, refresh validation key redaction, manual-evidence classification, and refresh-path toast locators are now fixed in the worktree.
- `refresh_start_was_accepted(...)` now gates both the manual-evidence scenario classification and whether duplicate/polling checks should run. If the first refresh call only hit an already-running refresh, the helper now correctly leaves the "successful refresh" scenario unproven instead of attributing somebody else's refresh to the current run.
- `HttpObservation.ok` still only means transport success. Any logic that needs to detect backend-contract failures must continue to inspect `status_code` explicitly; the helper now does this for refresh-status polling.
- `src/frontend/tests/e2e/refresh-path.spec.ts` now passes targeted local execution, but its `/api/sources` and `/api/stats` fixtures are still simpler than the real backend aggregation logic, and the timeout test still couples itself to a polling cadence threshold.
- Trusted-machine evidence is still blocked inside Codex by the lack of a real `NEWS_API_KEY` and a real browser session. The mocked Playwright suite is useful contract coverage, but it does not replace the real local evidence pass.
- This implementation pass reran local backend tests, frontend typecheck, and the mocked refresh-path Playwright slice; it did not execute the helper against a real key or complete the manual browser evidence checklist.
- Backend tests that set `DATABASE_URL` before importing app modules should continue to run in separate Python processes. Do not collapse `test_api_smoke` and `test_refresh_processing` into one interpreter invocation.
- Keep the legacy boundary intact. If upcoming work needs v1 behavior, recover it from git history or `READMEOLD.md`; do not recreate root-level runtime files as part of unrelated v2 cleanup.

## 5. Next recommended build slice
- Take the remaining `src/frontend/tests/e2e/refresh-path.spec.ts` fixture drift first. It is the highest-signal remaining code-level confidence gap because the targeted spec now passes, but its helpers still do not fully model backend aggregation semantics.
- After that, resolve the key-handling/doc contract so `README.md`, `AGENTS.md`, `src/frontend/README.md`, and the manual-evidence helper all describe the same supported local workflow.
- Once those P2 items are closed, finish the trusted-machine Phase 3 evidence pass on a real local machine and paste the concrete observed outcomes back into this file.
