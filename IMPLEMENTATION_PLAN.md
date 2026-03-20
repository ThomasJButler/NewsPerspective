# IMPLEMENTATION_PLAN.md

## 1. Current status summary and code review

Updated on 2026-03-20 (sixth pass, Claude Code Opus 4.6, `master` branch). This pass merged `v2.0-UX` into `master` via PR #5, deleted stale v2 branches, and transitioned to Phase 6.

### Verified runtime state
- `POST /api/refresh` requires a user-supplied `X-News-Api-Key`. The backend does not read a server-side `NEWS_API_KEY`.
- Cached read-only endpoints work without a key.
- `src/backend/services/article_processor.py` does one AI call per new article and stores sentiment, rewrite output, TLDR, and Good News state together.
- Good News exclusions for `sports`, `entertainment`, and detected `politics` are enforced in backend logic (`utils/good_news.py`) and reflected in frontend behavior.
- Exception chaining (`raise ... from exc`) is correctly used in `src/backend/routers/sources.py` lines 166 and 174.
- Refresh timeout resume behavior is implemented in `src/frontend/app/page.tsx` (lines 294-356) and helper-covered in `src/frontend/lib/refresh-status.test.mjs`.
- The visible-headline fallback lives in `src/frontend/lib/headlines.ts` (`getVisibleHeadline()`).
- Root-level v1 runtime files remain absent. Legacy reference lives in `READMEOLD.md` and git history only.
- Backend CORS allows `http://localhost:3000` only. Adequate for local development; will need updating if a deployment target is added.
- No TODO/FIXME/HACK markers in production code (backend or frontend). All TODO markers are intentional placeholders in the manual-evidence capture helper script.
- Backend article model schema matches `specs/BACKEND.md` persistence model exactly.
- Frontend proxy (`next.config.ts`) rewrites `/api/*` to `BACKEND_ORIGIN` (default `http://localhost:8000`), matching spec.
- All frontend components, hooks, types, and library files documented in `specs/FRONTEND.md` exist in the tree.
- `specs/AI_PROMPTS.md` system prompt and user prompt template match actual strings in `src/backend/services/ai_service.py` exactly. No drift.
- Next.js version in `package.json` is `16.1.7`, matching `specs/FRONTEND.md`.

### Validation snapshot (2026-03-20, post headline rewrite visibility investigation)
- `npm run lint` — passed.
- `npm run typecheck` — passed.
- `npx playwright test` — **11/11 passed** (both `cached-browse.spec.ts` and `refresh-path.spec.ts`).
- Backend: `test_refresh_processing` **12/12 passed** (9 existing + 3 new validation tests). `test_api_smoke` 29, `test_config` 4, `test_manual_integration_evidence` 14 — all passed. Total: **59 backend tests**.

### Worktree state
`master` working tree is **clean**. Branch is **up to date** with `origin/master`.

### GitHub state (verified 2026-03-20)
- ~~**PR #5**~~ Merged 2026-03-20. `v2.0-UX` → `master` (8 commits: test fix, security merge, spec alignment, e2e fix, package-lock, plan update). Fast-forward merge.
- ~~**PR #4**~~ Merged 2026-03-20. Security dependency bump.
- No open issues or PRs.
- GitHub repo description is current v2 language.

### Branch state
**`master`** is the sole active branch. All v2 feature branches have been merged and deleted:
- ~~`v2.0-UX`~~ — merged via PR #5, deleted (local + remote).
- ~~`v2.0`~~ — deleted (local + remote). Content was in master via PR #3.
- ~~`v2.0-Codex`~~ — deleted (local + remote). Superseded.
- ~~`v2.0-Security`~~ — deleted (local + remote). Same as master.

Legacy remote-only branches remain: `v1.1`, `v1.2`, `v1.3`, `v1.4`. Kept for historical reference; safe to remove if desired.

### Open review findings
All prior P1/P2/P3 findings are resolved. No new code-spec mismatches found in fifth-pass verification. Code-spec alignment is strong across all active specs.

## 2. Active phase

**Phase 6 — UX polish.** Phase 5 is complete (`v2.0-UX` merged to `master` via PR #5, stale branches cleaned up). Phase 6 follows `specs/ROADMAP.md` Near-Term Loop Order: headline rewrite visibility investigation, feed thumbnails, header alignment, and other visual refinements.

## 3. Ordered checklist

### Completed (Phase 5)
- [x] Full source verification (5 passes): backend model schema, routers, services, AI prompts, frontend components/hooks/lib/types, proxy config. Zero code-spec mismatches.
- [x] Test isolation fix in `test_refresh_processing.py` — committed `7190477`.
- [x] PR #4 security dependency bump — merged 2026-03-20.
- [x] Spec alignment: `FRONTEND.md` version string, project structure; `ROADMAP.md` loop order; validation command docs in `README.md`/`CLAUDE.md`/`AGENTS.md`.
- [x] GitHub repo description updated to v2 language.
- [x] Playwright e2e — 11/11 passed after fixing stale Good News toggle assertion.
- [x] Package-lock.json committed (`ce49ded`).

- [x] PR #5: merge `v2.0-UX` → `master` — merged 2026-03-20 (fast-forward, 8 commits).
- [x] Branch cleanup: deleted local+remote `v2.0`, `v2.0-Codex`, `v2.0-Security`, `v2.0-UX`. Legacy `v1.*` remotes retained.
- [x] Legacy boundary: `READMEOLD.md` and git history only; no new root-level v1 files.

### Active (Phase 6 — UX polish)
- [x] [P2] **Evaluate headline rewrite visibility.** Investigated end-to-end. No display bug: `getVisibleHeadline()` correctly surfaces rewrites. "Not always appearing" is by-design — the AI only rewrites sensationalized/misleading headlines; fair, factual headlines keep their original form. Fixed one robustness gap: `_validate_result` now normalizes `needs_rewrite` to `false` when `rewritten_title` is null/empty, preventing `rewritten_count` stat inflation. Added 3 unit tests.
- [x] [P3] **Add article card thumbnails.** Per `specs/ROADMAP.md`: "Add a small thumbnail to article cards in the main feed." Added a 96×96 thumbnail on the right side of each article card using `next/image` with `unoptimized` (matching detail page pattern). Hidden on mobile (`hidden sm:block`), gracefully absent when `image_url` is null. Validated with `npm run lint` and `npm run typecheck`.
- [x] [P3] **Header/feed layout alignment.** Per `specs/ROADMAP.md`: "Align the header content with the article stack so the layout feels tidy and streamlined." Added `max-w-3xl` to the header container div in `header.tsx` so the header content width matches the `max-w-3xl` main content area in `page.tsx`. Validated with `npm run lint` and `npm run typecheck`.
- [ ] [P3] **Evaluate broader roadmap items** (content guardrails, country-aware reading, topic filtering, About modal, accessibility audit) against current codebase maturity before promoting any into active specs.

## 4. Notes / discoveries that matter for the next loop

- **SOCKS proxy test isolation.** The `AIService.__init__` mock fix prevents `OpenAI()` client setup from leaking into the test path. Root cause is environment proxy variables (`ALL_PROXY`), not a missing dependency. Do not install `socksio` or clear proxy vars as a workaround.
- **Test count.** Full backend count is 59 tests across `test_api_smoke` (29), `test_refresh_processing` (12), `test_manual_integration_evidence` (14), and `test_config` (4).
- **Frontend helper tests** use `node --test --experimental-strip-types`. Experimental warnings are expected and not regressions.
- **`logs/phase3_manual_integration_report.md`** is present and matches the v2 boundary. Refresh only if the refresh contract or visible refresh UI copy changes.
- **Manual evidence helper** intentionally leaves human-fill `TODO` placeholders. That is the design, not a broken implementation.
- **Code-spec alignment is strong.** Fifth-pass full source verification found zero mismatches between active specs and running code.
- **`specs/ROADMAP.md` exception-chaining reference** was already removed in a prior pass. The ROADMAP no longer incorrectly says exception chaining is pending.

## 5. Next recommended build slice

**Evaluate broader roadmap items.**

Per the Phase 6 checklist: evaluate content guardrails, country-aware reading, topic filtering, About modal, and accessibility audit against current codebase maturity before promoting any into active specs.

1. Review each roadmap-only item in `specs/ROADMAP.md` against the current backend/frontend code.
2. Assess implementation complexity and prerequisites for each.
3. Recommend a prioritized subset to promote into active specs, or document why items should remain roadmap-only for now.
