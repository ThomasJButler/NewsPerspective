# IMPLEMENTATION_PLAN.md

## 1. Current status summary and code review

Updated on 2026-03-20 (fifth pass, Claude Code Opus 4.6, `v2.0-UX` branch). This pass corrected stale worktree/branch state descriptions and identified the natural next milestone: landing `v2.0-UX` work on `master`.

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

### Validation snapshot (2026-03-20, post Playwright e2e fix)
- `npm run lint` — passed.
- `npm run typecheck` — passed.
- `npx playwright test` — **11/11 passed** (both `cached-browse.spec.ts` and `refresh-path.spec.ts`).
- Backend test suites not re-run this pass (no backend changes).

### Worktree state
`v2.0-UX` working tree is **clean**. Branch is **up to date** with `origin/v2.0-UX`.

### GitHub state (verified 2026-03-20)
- No open issues or PRs.
- ~~**PR #4**~~ Merged 2026-03-20. Security dependency bump: `next` 16.1.6→16.1.7, `flatted` 3.3.4→3.4.2, `hono` 4.12.5→4.12.8.
- GitHub repo description is current v2 language.

### Branch state (corrected this pass)
**`v2.0-UX` is 7 commits ahead of `master`** (`ce49ded` vs `323f594`). Master has no commits that are not in `v2.0-UX`. The 7 commits contain:
1. `7190477` — Test isolation fix (mock `AIService.__init__` in Good News persistence tests)
2. `69491dc` — Merge `origin/master` into `v2.0-UX` (pulled PR #4)
3. `8fd50e3` — Merge PR #4 security bump and update specs/plan
4. `fa24deb` — Align specs and validation docs with shipped codebase
5. `2fa182a` — Update GitHub repo description to v2 and refresh plan
6. `6dd1826` — Fix stale e2e assertion and run full Playwright validation (11/11)
7. `ce49ded` — Update package-lock.json

All of this work is validated and should land on `master`.

Other local and remote v2 branches (all safe to delete after `v2.0-UX` lands):
- `v2.0` → `d50943e` — Source branch for PR #3. All content in `master` via merge commit.
- `v2.0-Codex` → `e83a153` — Far behind master (38+ commits). All content superseded.
- `v2.0-Security` → `323f594` — Same as `master`.

Legacy remote-only branches: `v1.1`, `v1.2`, `v1.3`, `v1.4`. Consider removing after the merge.

### Open review findings
All prior P1/P2/P3 findings are resolved. No new code-spec mismatches found in fifth-pass verification. Code-spec alignment is strong across all active specs.

## 2. Active phase

**Phase 5 → Phase 6 transition.** Phase 5 (commit hygiene, security maintenance, documentation alignment, validation boundaries) is functionally complete. The only remaining Phase 5 items are landing `v2.0-UX` on `master` and cleaning up stale branches.

After that, Phase 6 is **UX polish** per `specs/ROADMAP.md` Near-Term Loop Order: feed thumbnails, header alignment, headline rewrite visibility, and other visual refinements.

## 3. Ordered checklist

### Completed (Phase 5)
- [x] Full source verification (5 passes): backend model schema, routers, services, AI prompts, frontend components/hooks/lib/types, proxy config. Zero code-spec mismatches.
- [x] Test isolation fix in `test_refresh_processing.py` — committed `7190477`.
- [x] PR #4 security dependency bump — merged 2026-03-20.
- [x] Spec alignment: `FRONTEND.md` version string, project structure; `ROADMAP.md` loop order; validation command docs in `README.md`/`CLAUDE.md`/`AGENTS.md`.
- [x] GitHub repo description updated to v2 language.
- [x] Playwright e2e — 11/11 passed after fixing stale Good News toggle assertion.
- [x] Package-lock.json committed (`ce49ded`).

### Active
- [ ] [P2] **Open PR to merge `v2.0-UX` → `master`.** The branch has 7 validated commits (test fix, security merge, spec alignment, e2e fix, package-lock update). Master has no divergent commits. This is a clean fast-forward-eligible merge. Steps: (a) push is already done; (b) open PR from `v2.0-UX` to `master`; (c) validate CI if configured; (d) merge.
- [ ] [P3] **Branch cleanup.** After `v2.0-UX` merges to `master`: (a) delete local+remote `v2.0`, `v2.0-Codex`, `v2.0-Security`; (b) delete local+remote `v2.0-UX`; (c) evaluate whether legacy remote branches `v1.1`–`v1.4` should be kept for historical reference or removed.
- [ ] [P3] **Keep the legacy boundary explicit.** Use `READMEOLD.md` or git history for v1 reference, not new root-level files.

### Upcoming (Phase 6 — UX polish)
- [ ] [P2] **Evaluate headline rewrite visibility.** Per `specs/ROADMAP.md`: "Investigate and fix the current-feed behavior where rewritten headlines are not always appearing as expected." Verify whether `getVisibleHeadline()` correctly surfaces rewrites in the article card list view, or if there is a display/data issue.
- [ ] [P3] **Add article card thumbnails.** Per `specs/ROADMAP.md`: "Add a small thumbnail to article cards in the main feed." The backend already stores `image_url`; the frontend `article-card.tsx` needs to render it.
- [ ] [P3] **Header/feed layout alignment.** Per `specs/ROADMAP.md`: "Align the header content with the article stack so the layout feels tidy and streamlined."
- [ ] [P3] **Evaluate broader roadmap items** (content guardrails, country-aware reading, topic filtering, About modal, accessibility audit) against current codebase maturity before promoting any into active specs.

## 4. Notes / discoveries that matter for the next loop

- **SOCKS proxy test isolation.** The `AIService.__init__` mock fix prevents `OpenAI()` client setup from leaking into the test path. Root cause is environment proxy variables (`ALL_PROXY`), not a missing dependency. Do not install `socksio` or clear proxy vars as a workaround.
- **Test count.** Full backend count is 56 tests across `test_api_smoke` (29), `test_refresh_processing` (9), `test_manual_integration_evidence` (14), and `test_config` (4).
- **Frontend helper tests** use `node --test --experimental-strip-types`. Experimental warnings are expected and not regressions.
- **`logs/phase3_manual_integration_report.md`** is present and matches the v2 boundary. Refresh only if the refresh contract or visible refresh UI copy changes.
- **Manual evidence helper** intentionally leaves human-fill `TODO` placeholders. That is the design, not a broken implementation.
- **Code-spec alignment is strong.** Fifth-pass full source verification found zero mismatches between active specs and running code.
- **`specs/ROADMAP.md` exception-chaining reference** was already removed in a prior pass. The ROADMAP no longer incorrectly says exception chaining is pending.

## 5. Next recommended build slice

**Open PR to merge `v2.0-UX` → `master`.**

1. Open a PR from `v2.0-UX` to `master` summarizing the 7 commits (test fix, security merge, spec/doc alignment, e2e fix, package-lock update).
2. Merge the PR (fast-forward eligible — no conflicts expected).
3. After merge, delete stale branches: `v2.0`, `v2.0-Codex`, `v2.0-Security`, `v2.0-UX` (local and remote).
4. Evaluate legacy `v1.*` remote branches for deletion.
5. Transition to Phase 6 (UX polish): start with headline rewrite visibility investigation.
