# IMPLEMENTATION_PLAN.md

## 1. Current status summary and code review

Updated on 2026-03-20 (fourth pass, Claude Code Opus 4.6, `v2.0-UX` branch). This pass independently re-verified all prior findings, corrected one factual error in the branch state description, and confirmed no code changes since the third pass.

### Verified runtime state
- `POST /api/refresh` requires a user-supplied `X-News-Api-Key`. The backend does not read a server-side `NEWS_API_KEY`.
- Cached read-only endpoints work without a key.
- `src/backend/services/article_processor.py` does one AI call per new article and stores sentiment, rewrite output, TLDR, and Good News state together.
- Good News exclusions for `sports`, `entertainment`, and detected `politics` are enforced in backend logic (`utils/good_news.py`) and reflected in frontend behavior.
- Exception chaining (`raise ... from exc`) is correctly used in `src/backend/routers/sources.py` lines 166 and 174. The ROADMAP still incorrectly says this is pending.
- Refresh timeout resume behavior is implemented in `src/frontend/app/page.tsx` (lines 294-356) and helper-covered in `src/frontend/lib/refresh-status.test.mjs`.
- The visible-headline fallback lives in `src/frontend/lib/headlines.ts` (`getVisibleHeadline()`).
- Root-level v1 runtime files remain absent. Legacy reference lives in `READMEOLD.md` and git history only.
- Backend CORS allows `http://localhost:3000` only. Adequate for local development; will need updating if a deployment target is added.
- No TODO/FIXME/HACK markers in production code (backend or frontend). All TODO markers are intentional placeholders in the manual-evidence capture helper script.
- Backend article model schema matches `specs/BACKEND.md` persistence model exactly.
- Frontend proxy (`next.config.ts`) rewrites `/api/*` to `BACKEND_ORIGIN` (default `http://localhost:8000`), matching spec.
- All frontend components, hooks, types, and library files documented in `specs/FRONTEND.md` exist in the tree — plus 7 additional shipped files the spec omits (see review findings below).
- **`specs/AI_PROMPTS.md` verified.** System prompt and user prompt template match the actual strings in `src/backend/services/ai_service.py` exactly, word-for-word. No drift.

### Validation snapshot (2026-03-20, post PR #4 merge)
After merging PR #4 (security dependency bump) into master and pulling into `v2.0-UX`:
- `npm run lint` — passed.
- `npm run typecheck` — passed.
- `node --test --experimental-strip-types lib/headlines.test.mjs lib/refresh-status.test.mjs` — **7 tests passed**.
- Backend test suites not re-run (no backend changes in this slice).
- Playwright e2e was not exercised in this pass (needs live ports).

### Worktree state
`v2.0-UX` has merged `origin/master` (which now includes PR #4). Local branch is ahead of `origin/v2.0-UX` by 4 commits (test isolation fix + PR #4 merge commit + merge of master). Uncommitted local changes:
1. **`IMPLEMENTATION_PLAN.md`** — This file (planning updates).
2. **`specs/FRONTEND.md`** — Version string updated from `16.1.6` to `16.1.7`.

### GitHub state (verified 2026-03-20)
- ~~**PR #4**~~ Merged 2026-03-20. Security dependency bump: `next` 16.1.6→16.1.7, `flatted` 3.3.4→3.4.2, `hono` 4.12.5→4.12.8. Validated locally (lint, typecheck, 7/7 helper tests) before merging. `specs/FRONTEND.md` version string updated to match.
- No open issues or PRs.
- **GitHub repo description is stale.** It still reads "A Python-based application designed to fetch news articles using the NewsAPI, rewrite headlines into a more positive tone using Azure OpenAI, and upload the rewritten content to Azure Search for indexing." This is v1 language (Azure OpenAI, Azure Search). Should be updated to reflect v2 architecture.

### Branch state (corrected from prior pass)
Local and remote v2 branches:
- `v2.0` → `d50943e` — The source branch for PR #3. All its content is in `master` via merge commit `323f594`. One merge-commit behind master. Safe to delete.
- `v2.0-Codex` → `e83a153` ("Set up docker configuration") — Far behind master (38+ commits). All its content has been superseded. Safe to delete.
- `v2.0-Security` → `323f594` — Same as `master`. Safe to delete.
- `v2.0-UX` → `323f594` — Same as `master`. Current working branch; keep until uncommitted work is landed, then evaluate.

Legacy remote-only branches: `v1.1` (`b37a039`), `v1.2` (`986ba68`), `v1.3` (`55cbb6d`), `v1.4` (`54187ab`). Consider cleaning up stale branches after the test fix is committed and PR #4 is merged.

### Open review findings
- ~~**[P1] Uncommitted test fix.**~~ Resolved — committed as `7190477` on `v2.0-UX`.
- ~~**[P1] Security dependency bump.**~~ Resolved — PR #4 merged 2026-03-20. `specs/FRONTEND.md` version string updated.
- **[P2] `specs/ROADMAP.md` is stale.** Its `Near-Term Loop Order` (lines 182-188) still says the next loop should make exception chaining explicit in `sources.py` — but that work is already done (lines 166, 174).
- **[P2] `specs/FRONTEND.md` is stale.** Its `Current Project Structure` (lines 17-52) omits 7 shipped files: `components/refresh-status-card.tsx`, `components/toaster.tsx`, `lib/headlines.ts`, `lib/refresh-status.ts`, `lib/headlines.test.mjs`, `lib/refresh-status.test.mjs`, and `types/article.ts`.
- **[P3] Validation command docs omit `test_config`.** `README.md`, `CLAUDE.md`, and `AGENTS.md` all list only 3 of 4 backend test suites in their validation commands, omitting `src.backend.tests.test_config`. The suite exists and passes (4 tests) but a fresh loop runner following the docs would not discover it.
- **[P3] GitHub repo description is stale v1 language.** (See GitHub state above.)

## 2. Active phase

Phase 5: commit hygiene, security maintenance, documentation alignment, and validation boundaries.

All earlier correctness fixes are in place. The immediate priorities are: (1) commit the orphaned test fix, (2) review/merge the security dependency PR, (3) repair stale specs and docs, (4) branch cleanup.

## 3. Ordered checklist

### Completed
- [x] [P1] Re-read `AGENTS.md`, `CLAUDE.md`, `IMPLEMENTATION_PLAN.md`, `README.md`, all active specs, and source code.
- [x] [P1] Inspect backend/frontend source to verify refresh contract, cached read-only contract, Good News exclusions, exception chaining, visible-headline helper path, and refresh timeout resume behavior.
- [x] [P1] Run focused validation snapshot: all backend suites (56 tests across 4 files), frontend lint/typecheck, frontend helper tests (7 tests).
- [x] [P1] Fix test isolation in `test_refresh_processing.py`: Added `AIService.__init__` no-op mocks alongside existing `analyse_article` mocks in sports and politics Good News persistence tests.
- [x] [P2] Review `README.md` and `src/frontend/README.md` against the runtime and active specs. No blockers found.
- [x] [P2] Verify GitHub issue/PR state. Found PR #4 (security dependency bump).
- [x] [P2] Second-pass full source verification: backend model schema, all routers, all services, frontend components/hooks/lib/types, proxy config. No code-vs-spec mismatches found.
- [x] [P3] Verify `specs/AI_PROMPTS.md` prompt text against actual strings in `src/backend/services/ai_service.py`. **Result: exact match, no drift.** System prompt (lines 11-27) and user prompt template (lines 29-44) are word-for-word identical to the spec.
- [x] Correct branch state description. Prior plan incorrectly said all four v2 branches are at master's commit; `v2.0` is at `d50943e` and `v2.0-Codex` is at `e83a153`.

### Active
- [x] [P1] **Commit the test isolation fix.** Committed as `7190477` on `v2.0-UX`. All 9 `test_refresh_processing` tests pass. Only the test file was staged; `IMPLEMENTATION_PLAN.md` excluded.
- [x] [P1] **Review and merge PR #4** (dependabot security bump: `next`, `flatted`, `hono`). Validated on PR branch (lint, typecheck, 7/7 helper tests). Merged 2026-03-20. Master pulled into `v2.0-UX`. Post-merge validation passed (lint, typecheck, 7/7 helper tests).
- [x] [P2] After PR #4 merges, update `specs/FRONTEND.md` line 7 version string from `16.1.6` to `16.1.7`. Done.
- [ ] [P2] **Update `specs/ROADMAP.md`** `Near-Term Loop Order` section. Remove the stale reference to exception-chaining cleanup (already done). Replace with the actual current sequence: spec alignment → Playwright validation → UX polish.
- [ ] [P2] **Update `specs/FRONTEND.md`** `Current Project Structure` to list shipped files: `components/refresh-status-card.tsx`, `components/toaster.tsx`, `lib/headlines.ts`, `lib/refresh-status.ts`, `lib/headlines.test.mjs`, `lib/refresh-status.test.mjs`, `types/article.ts`.
- [ ] [P2] After spec edits land, validate with frontend lint/typecheck and frontend helper tests.
- [ ] [P3] **Update validation command docs.** Add `src.backend.tests.test_config` to the backend validation commands in `README.md`, `CLAUDE.md`, and `AGENTS.md`.
- [ ] [P3] **Update GitHub repo description.** Replace stale v1 language (Azure OpenAI, Azure Search) with a v2 summary (FastAPI + Next.js, OpenAI, SQLite).
- [ ] [P3] Run Playwright e2e on a machine that can bind ports 8000/3000, or use `npm run test:e2e:reuse` against an already-running local stack.
- [ ] [P3] **Branch cleanup.** After the test fix commit lands and PR #4 merges: (a) delete `v2.0`, `v2.0-Codex`, and `v2.0-Security` (all fully merged or superseded); (b) evaluate whether `v2.0-UX` should be kept or merged to master and deleted; (c) evaluate whether legacy remote branches `v1.1`–`v1.4` should be kept for historical reference or removed.
- [ ] [P3] Keep the legacy boundary explicit during doc cleanup. Use `READMEOLD.md` or git history for v1 reference, not new root-level files.

## 4. Notes / discoveries that matter for the next loop

- ~~**Worktree discipline.**~~ Resolved — the orphaned test fix was committed as `7190477` on `v2.0-UX` (2026-03-20).
- ~~**Security PR urgency.**~~ Resolved — PR #4 merged 2026-03-20.
- ~~**Transitive dependency note.**~~ Resolved — all three deps updated via PR #4 merge.
- **SOCKS proxy test isolation.** The `AIService.__init__` mock fix prevents `OpenAI()` client setup from leaking into the test path. The root cause is environment proxy variables (`ALL_PROXY`), not a missing dependency. Do not install `socksio` or clear proxy vars as a workaround.
- **Test count correction.** The prior plan said "52 tests" because validation ran only 3 of 4 backend test suites. The full count is 56 tests across `test_api_smoke` (29), `test_refresh_processing` (9), `test_manual_integration_evidence` (14), and `test_config` (4). The docs should list all 4 suites.
- **Frontend helper tests** use `node --test --experimental-strip-types`. Experimental warnings are expected and not regressions.
- **`logs/phase3_manual_integration_report.md`** is still present and matches the v2 boundary. Refresh only if the refresh contract or visible refresh UI copy changes.
- **Manual evidence helper** intentionally leaves human-fill `TODO` placeholders. That is the design, not a broken implementation.
- **Branch convergence (corrected).** `v2.0-Security` and `v2.0-UX` are at `323f594` (same as master). `v2.0` is at `d50943e` (its pre-merge head; all content in master via merge commit). `v2.0-Codex` is at `e83a153` ("Set up docker configuration"), 38+ commits behind master — all its content has been superseded. Legacy remote branches `v1.1`–`v1.4` also exist on origin. All non-UX v2 branches are safe to delete; `v2.0-UX` should be evaluated once its uncommitted work lands.
- **Code-spec alignment is strong.** Fourth-pass full source verification (including AI_PROMPTS.md) found zero mismatches between active specs and running code. The only spec issues are the omissions documented in the review findings (stale ROADMAP loop order, missing FRONTEND.md file listings).

## 5. Next recommended build slice

**Spec alignment: update `specs/ROADMAP.md` and `specs/FRONTEND.md`.**

1. Update `specs/ROADMAP.md` Near-Term Loop Order — remove stale exception-chaining reference, replace with current sequence.
2. Update `specs/FRONTEND.md` Current Project Structure — add the 7 shipped files the spec omits.
3. Update validation command docs (`README.md`, `CLAUDE.md`, `AGENTS.md`) — add `test_config` to the backend test suite list.
4. Validate with frontend lint/typecheck and helper tests after spec edits.
