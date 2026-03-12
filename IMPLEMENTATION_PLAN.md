# IMPLEMENTATION_PLAN.md

## 1. Current status summary and code review
- Updated on 2026-03-12 after implementing the home-page persistent refresh-status slice, rerunning targeted frontend validation, and refreshing the relevant frontend spec/plan notes for the shipped behavior.
- Priority levels used below:
  - `P1`: next-loop work that closes a user-visible product/spec gap or correctness risk.
  - `P2`: important follow-up work that depends on `P1` or needs source-of-truth alignment.
  - `P3`: low-risk cleanup, documentation polish, or non-blocking review follow-up.
- GitHub state checked during this planning pass:
  - `gh issue list --state open -L 20 --json number,title,state,url` returned `[]`.
  - `gh pr status` shows PR `#3 V2.0` on branch `v2.0` with checks passing.
  - PR `#3` review history confirms the earlier refresh-path, manual-evidence, and Playwright findings are already reflected in the checked-out code. The remaining review findings still visible in source are limited to backend router cleanup: SQLAlchemy boolean comparisons still use `== True` in `src/backend/routers/articles.py` and `src/backend/routers/sources.py`, and `src/backend/routers/sources.py` still re-raises refresh-validation failures without explicit exception chaining.
- Validation rerun during this build slice:
  - `cd src/frontend && npm run lint` passed.
  - `cd src/frontend && npm run typecheck` passed.
  - `cd src/frontend && npx playwright test tests/e2e/refresh-path.spec.ts` passed.
- Verified implementation state:
  - Phase 3 trusted-machine evidence is complete and stored in `logs/phase3_manual_integration_report.md`. The repo-local report covers cached browse without a key, invalid-key handling, accepted real-key refresh, duplicate refresh short-circuiting, refresh-status polling, terminal completion, reuse-path Playwright (`4 passed (9.3s)`), and the manual browser refresh outcome.
  - The v2 boundary is still intact. The removed root-level v1 runtime files have not reappeared; legacy reference remains limited to `READMEOLD.md` and git history.
  - The live backend contract still matches the active specs: cached read-only article endpoints work without a NewsAPI key, refresh requires `X-News-Api-Key`, and each article is processed with one AI call that returns sentiment, rewrite data, TLDR, and the good-news flag.
  - The home route now renders a persistent refresh-status card above the stats bar and feed. It combines durable `stats.latest_fetch` data with the volatile `/api/refresh/status` snapshot so `processing`, terminal `completed`, terminal `failed`, and restart-to-`idle` cases all stay visible beyond transient toasts.
  - `specs/FRONTEND.md` now documents the shipped persistent refresh-status behavior, including the restart case where `latest_fetch` survives but the in-memory refresh tracker resets to `idle`.
  - Good News roadmap exclusions for `sports`, `entertainment`, and `politics` are still not enforced in backend classification/filtering or frontend copy. Current runtime continues to trust the AI-provided `is_good_news` flag and the existing `good_news_only` filter.
  - `specs/ROADMAP.md` still declares broader content guardrails for `war`, `suicide`, `depression`, `death`, and `grief`, but those rules are not implemented in runtime behavior or promoted into the active backend/frontend specs. The Phase 3 evidence artifact still shows war-related stories in the normal feed, so this remains an explicit roadmap-to-runtime mismatch.
  - Documentation status drift remains: `README.md`, `src/frontend/README.md`, and `specs/BACKEND.md` still describe trusted-machine refresh evidence as remaining work or as something still tracked separately in the plan, even though the evidence artifact is already complete on disk.
  - One previously tracked review nit is already resolved and should not stay open in this plan: `specs/OVERVIEW.md` already labels the ASCII architecture fence as `text`.

## 2. Active phase
Phase 4 frontend integration cleanup and source-of-truth alignment. Phase 3 evidence is closed. The first missing user-facing refresh-status surface in `src/frontend/` is now shipped, so the next build loop should move to the remaining doc/source-of-truth alignment work around Phase 3 evidence and current v2 runtime. Keep the root-level v2 boundary intact: if older behavior needs reference, use `READMEOLD.md` or git history instead of recreating removed legacy runtime files.

## 3. Ordered checklist with [ ] and [x]
- [x] [P1] Re-read repo operating docs, active specs, README context, current PR review state, and the relevant backend/frontend source before updating the plan.
- [x] [P1] Re-verify the current baseline with lightweight automated checks. Backend smoke, refresh-processing regressions, manual-evidence helper tests, frontend lint, and frontend typecheck all passed on 2026-03-12.
- [x] [P1] Confirm that Phase 3 trusted-machine evidence is actually complete on disk. `logs/phase3_manual_integration_report.md` is present and populated with the accepted real-key refresh flow, duplicate short-circuit, polling trail, terminal completion, reuse-path Playwright result, and manual browser outcome.
- [x] [P1] Preserve the v2 boundary. Root-level v1 runtime files remain absent from the checked-out repo.
- [x] [P1] Add a persistent refresh-status surface on the home page instead of relying only on transient toasts.
- [x] [P1] Reuse the existing frontend/backend contracts for that surface. Use `/api/stats.latest_fetch` as the durable last-success signal and `/api/refresh/status` only for live or most-recent in-process state; do not add backend endpoints for this slice.
- [x] [P1] Define and implement durable UI states for `processing`, `completed with new articles`, `completed with no new articles`, `failed`, and `idle after restart with a previous successful refresh`.
- [x] [P1] Handle process-restart semantics explicitly: if the backend returns `idle` because the in-memory tracker reset but `stats.latest_fetch` still exists, keep showing the durable last-success signal instead of implying refresh history was lost entirely.
- [x] [P1] Add focused frontend proof for the persistent refresh-status surface. Proof on 2026-03-12: `cd src/frontend && npm run lint`, `cd src/frontend && npm run typecheck`, and `cd src/frontend && npx playwright test tests/e2e/refresh-path.spec.ts`.
- [x] [P2] After the refresh-status surface lands, update `specs/FRONTEND.md` so it describes the shipped persistent refresh-status behavior instead of the current toast-only flow.
- [ ] [P2] Remove stale “remaining Phase 3 / tracked separately in the plan” wording from `README.md`, `src/frontend/README.md`, and `specs/BACKEND.md`, and point those references at `logs/phase3_manual_integration_report.md` where appropriate.
- [ ] [P2] Decide how the roadmap-only content guardrails (`war`, `suicide`, `depression`, `death`, `grief`) should be treated in v2 source-of-truth documents before changing behavior. Either promote them into active specs or mark them explicitly as future work so the roadmap and runtime stop disagreeing by implication.
- [ ] [P2] After the source-of-truth decision, enforce the Good News exclusions for `sports`, `entertainment`, and `politics` consistently in backend behavior and frontend UX copy.
- [ ] [P2] Resolve the `politics` detection rule before implementing that exclusion. `src/backend/services/news_fetcher.py` does not fetch a `politics` category from NewsAPI today, so this needs app-level topic mapping or broader topic classification rather than a simple fetch-category toggle.
- [ ] [P3] Apply the remaining backend router review cleanup by replacing SQLAlchemy boolean filters that still use `== True` with `.is_(True)` in `src/backend/routers/articles.py` and `src/backend/routers/sources.py`.
- [ ] [P3] Make refresh-validation exception chaining explicit in `src/backend/routers/sources.py` (`from exc` or `from None`) so the remaining review finding there is fully closed.

## 4. Notes / discoveries that matter for the next loop
- `logs/phase3_manual_integration_report.md` is now the canonical repo-local evidence artifact for Phase 3 completion. Do not keep carrying forward blocker language that says real-key/manual-browser validation is still pending unless a newer run contradicts it.
- The report's `Docs drift` row says `none` for the helper/browser flow it exercised, but that does not clear the stale project-status wording in `README.md`, `src/frontend/README.md`, and `specs/BACKEND.md`. Those files still need a follow-up wording pass.
- The next frontend slice does not need backend API work. `StatsResponse.latest_fetch` already exists in `src/backend/routers/sources.py`, `src/backend/schemas.py`, `src/frontend/lib/api.ts`, and `src/frontend/types/article.ts`. `GET /api/refresh/status` is already exposed and already used during active refresh polling in `src/frontend/app/page.tsx`.
- `src/frontend/app/page.tsx` now fetches `/api/refresh/status` on load to seed the persistent refresh-status card. Any future mocked refresh tests need to account for that initial request before user-triggered refresh polling begins.
- Hidden dependency for the refresh-status UI: `/api/refresh/status` is process-local and resets on backend restart, while `/api/stats.latest_fetch` is persisted in SQLite. The UI should treat `latest_fetch` as durable history and the refresh-status endpoint as volatile process state.
- Another refresh-status caveat: failed refresh state is also in-memory only. If the backend restarts after a failure, the UI can still show the last successful fetch time from `latest_fetch`, but it cannot reconstruct a durable failed refresh history without new backend persistence.
- Hidden dependency for the Good News exclusions: `sports` and `entertainment` can be enforced against current category data, but `politics` cannot be implemented by simply removing a NewsAPI category because the fetcher never receives one today.
- `specs/OVERVIEW.md` already contains the `text` fence label. Do not reopen that resolved review nit in later planning passes.
- In this Codex shell, `npm run lint` and `npm run typecheck` print `nvm` help text before the normal npm output but still exit `0`. Treat that as an environment quirk unless a repo-local cause is found.
- Keep legacy handling conservative. If a future slice needs v1 behavior for reference, inspect `READMEOLD.md` or git history instead of recreating deleted root-level runtime files.

## 5. Next recommended build slice
Remove the stale “Phase 3 still pending / tracked separately in the plan” wording from the remaining source-of-truth docs and keep the slice narrow:

1. Update `README.md`, `src/frontend/README.md`, and `specs/BACKEND.md` so they point at `logs/phase3_manual_integration_report.md` instead of describing trusted-machine evidence as unfinished or separately tracked.
2. Re-read those docs against the shipped runtime boundary: cached browse without a key, refresh via `X-News-Api-Key`, and the completed Phase 3 evidence artifact.
3. Run only the smallest doc-validation needed for that wording slice, then update this plan so the later Good News guardrail decisions remain the next functional work.
