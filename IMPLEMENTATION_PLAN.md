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

**Phase 7 — Feature buildout.** Phase 6 UX polish items are complete (headline rewrite visibility, feed thumbnails, header alignment, roadmap evaluation). Phase 7 promotes the highest-value roadmap items into active work based on the maturity assessment below.

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
- [x] [P3] **Upgrade article card layout.** Replaced 96×96 side thumbnails with full-width 16:9 banner images at top of cards. Added image error handling (broken URLs collapse gracefully). Added sentiment badges (positive/neutral/negative) to feed card metadata. Updated skeleton loading with image placeholder. All viewports including mobile.
- [x] [P3] **Header/feed layout alignment.** Per `specs/ROADMAP.md`: "Align the header content with the article stack so the layout feels tidy and streamlined." Added `max-w-3xl` to the header container div in `header.tsx` so the header content width matches the `max-w-3xl` main content area in `page.tsx`. Validated with `npm run lint` and `npm run typecheck`.
- [x] [P3] **Evaluate broader roadmap items** (content guardrails, country-aware reading, topic filtering, About modal, accessibility audit, processing visibility, Fact Checker Mode) against current codebase maturity. Assessment complete — see §3a below for findings and promoted items.

### Roadmap evaluation results (Phase 6 → Phase 7 gate)

| Item | Complexity | Prerequisites | Recommendation |
|------|-----------|---------------|----------------|
| Content guardrails | **Small** | None — keyword exclusion mechanism in `good_news.py` is proven and extensible | **Promote** — expand existing keyword lists for war/suicide/depression/death/grief |
| About modal | **Small** | None — ShadCN `Dialog` infrastructure proven via `settings-dialog.tsx` | **Promote** — pure UI, no backend changes, improves discoverability |
| Accessibility pass | **Small–Medium** | None — good foundation exists (aria-labels, live regions); gaps are CSS focus states and `prefers-reduced-motion` | **Promote** — foundational; should land before large new features |
| Topic filtering UI | **Medium–Small** | Backend `category` query param already works; need `/api/categories` endpoint + frontend `CategoryFilter` component | **Promote** — backend plumbing exists, mostly frontend UI work |
| Country-aware reading | **Medium** | ~~Requires new `country` DB column, pipeline changes, frontend selector~~ | **SHIPPED** — `country` column added, dual US+GB fetch, frontend country filter, article country badges |
| Processing visibility | **Medium–Large** | Requires in-flight article UI, skeleton states, progressive polling or SSE | **Defer** — heaviest lift; best done after simpler features prove the UX patterns |
| Fact Checker Mode | **Large** | Requires cross-source article matching, country filtering, comparison UI — depends on country-aware reading | **Defer** — depends on country and topic infrastructure not yet built |

### Active (Phase 7 — Feature buildout)
Promoted items in priority order:
- [ ] [P2] **Content guardrails.** Add keyword-based exclusions for war, suicide, depression, death, and grief to `good_news.py`. Expand `apply_good_news_rules()` and `good_news_filter_expression()`. Update frontend toggle hint. Add tests for new exclusions.
- [x] [P3] **About modal.** Created `about-modal.tsx` with ShadCN Dialog. Added About button (info icon) to header. Includes app explanation, "How it works" list, GitHub link, Buy Me a Coffee link, version/attribution/license footer.
- [ ] [P3] **Accessibility pass.** Add `prefers-reduced-motion` check to spinner animations. Ensure visible focus states via `focus-visible` utilities. Add semantic landmarks to main content area. Test keyboard navigation through all controls.
- [ ] [P3] **Topic filtering UI.** Add `/api/categories` endpoint returning category names and counts. Create `CategoryFilter` component (pattern matches `SourceFilter`). Wire into page state and URL query params.

## 4. Notes / discoveries that matter for the next loop

- **SOCKS proxy test isolation.** The `AIService.__init__` mock fix prevents `OpenAI()` client setup from leaking into the test path. Root cause is environment proxy variables (`ALL_PROXY`), not a missing dependency. Do not install `socksio` or clear proxy vars as a workaround.
- **Test count.** Full backend count is 59 tests across `test_api_smoke` (29), `test_refresh_processing` (12), `test_manual_integration_evidence` (14), and `test_config` (4).
- **Frontend helper tests** use `node --test --experimental-strip-types`. Experimental warnings are expected and not regressions.
- **`logs/phase3_manual_integration_report.md`** is present and matches the v2 boundary. Refresh only if the refresh contract or visible refresh UI copy changes.
- **Manual evidence helper** intentionally leaves human-fill `TODO` placeholders. That is the design, not a broken implementation.
- **Code-spec alignment is strong.** Fifth-pass full source verification found zero mismatches between active specs and running code.
- **`specs/ROADMAP.md` exception-chaining reference** was already removed in a prior pass. The ROADMAP no longer incorrectly says exception chaining is pending.

### Planned (Phase 8 — Open source launch + Article Comparison)

**Open source packaging:**
- [ ] [P2] **AGPLv3 LICENSE file.** Add to repo root. Update `package.json` license field.
- [ ] [P2] **README overhaul.** Rewrite for open-source audience: hero section, quick-start guide (< 5 min), personalisation section, Claude prompt template for customising preferences/triggers, architecture overview, premium API note, contributing guidelines with CLA mention.
- [ ] [P3] **Demo video.** Screen recording with OBS, edit with DaVinci Resolve, upload to YouTube, link from README and About modal.

**Article Comparison feature:**
- [ ] [P3] **Article Comparison.** New `/comparison` page showing how the same story is framed differently across sources/countries. Backend: `GET /api/comparison` (fuzzy title matching to group same-story articles), `POST /api/comparison/analyse` (one AI call per group evaluating fear tactics, exaggeration, misinformation, balanced/biased language). Frontend: side-by-side card layout with AI analysis panel and colour-coded framing indicators. Test with 2 article groups: 1 controversial + 1 positive.

**Future considerations:**
- [ ] [P4] **Pluggable news source architecture.** Abstract NewsAPI integration so alternative providers (NewsData.io at $21/month, Guardian API free, BBC RSS free) can be swapped in.
- [ ] [P4] **User-configurable content guardrails.** Expand beyond hardcoded exclusions to let users specify trigger words and topics to avoid.

## 5. Next recommended build slice

**Content guardrails** — then **AGPLv3 LICENSE + README overhaul**.

Content guardrails first:

1. Add keyword tuples for each guardrail category in `good_news.py`.
2. Create helper functions matching the `is_politics_story()` pattern.
3. Update `apply_good_news_rules()` to apply the new exclusions.
4. Update `good_news_filter_expression()` SQL filter to include new keyword checks.
5. Update frontend `good-news-toggle.tsx` hint text to reflect expanded exclusions.
6. Add unit tests for each new exclusion category.
7. Update `specs/BACKEND.md` and `specs/ROADMAP.md` to reflect that these guardrails are now shipped.

Then LICENSE + README for open source readiness.

## 6. Notes from 2026-03-20 session (card layout + country + open source planning)

- **NewsAPI free tier cannot be used in production** (ToS prohibit it, CORS blocks deployed sites). Self-hosted personal use with user's own key is fine.
- **NewsAPI Business plan is $449/month** with no middle tier. Cheapest alternative: NewsData.io at $21/month. Free alternative: Guardian API + BBC RSS (UK-only, real-time).
- **License recommendation: AGPLv3** with dual licensing. Prevents commercial free-riding while keeping it genuinely open source. CLA needed if accepting outside PRs.
- **Demo video: use OBS screen recording** not Remotion. Remotion is 20-35 hours for first video vs 2-4 hours for screen recording. Only worthwhile for ongoing video production.
- **Dual US+GB fetch doubles API usage** from ~7 to ~14 requests per refresh. Still well within the 100/day free limit for personal use (~7 refreshes/day).
- **Article Comparison is the differentiator.** Few apps do cross-source/country AI framing analysis. Even as a 2-article proof of concept, this is shareable and unique.
