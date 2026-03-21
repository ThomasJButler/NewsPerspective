# IMPLEMENTATION_PLAN.md

## 1. Current status summary and code review

Updated on 2026-03-21 (seventh pass, Claude Code Opus 4.6, `v3.0` branch).

### Verified runtime state
- `POST /api/refresh` requires a user-supplied `X-News-Api-Key`. The backend does not read a server-side `NEWS_API_KEY`.
- Cached read-only endpoints work without a key.
- `src/backend/services/article_processor.py` does one AI call per new article and stores sentiment, rewrite output, TLDR, and Good News state together.
- Good News exclusions for `sports`, `entertainment`, and detected `politics` are enforced in backend logic (`utils/good_news.py`) and reflected in frontend behavior.
- Country support is end-to-end: `country` column in DB with migration, dual US+GB fetch in `news_fetcher.py`, country query param on `GET /api/articles`, `CountryFilter` component in frontend, country badges on article cards.
- About modal (`about-modal.tsx`) shows v3.0.0, explains the app, includes GitHub and Buy Me a Coffee links.
- Article cards use full-width 16:9 banner images with error fallback, sentiment badges, and country badges.
- Header content aligns with article feed via `max-w-3xl`.
- Exception chaining (`raise ... from exc`) is correctly used in `src/backend/routers/sources.py`.
- Refresh timeout resume behavior is implemented in `src/frontend/app/page.tsx` and helper-covered in `src/frontend/lib/refresh-status.test.mjs`.
- The visible-headline fallback lives in `src/frontend/lib/headlines.ts` (`getVisibleHeadline()`).
- Root-level v1 runtime files remain absent. Legacy reference lives in `READMEOLD.md` and git history only.
- Backend CORS allows `http://localhost:3000` only. Adequate for local development; will need updating if a deployment target is added.
- No TODO/FIXME/HACK markers in production code (backend or frontend).
- Backend article model schema matches `specs/BACKEND.md` persistence model exactly.
- Frontend proxy (`next.config.ts`) rewrites `/api/*` to `BACKEND_ORIGIN` (default `http://localhost:8000`), matching spec.
- All frontend components, hooks, types, and library files documented in `specs/FRONTEND.md` exist in the tree.
- `specs/AI_PROMPTS.md` system prompt and user prompt template match actual strings in `src/backend/services/ai_service.py` exactly. No drift.
- Next.js version in `package.json` is `16.1.7`, matching `specs/FRONTEND.md`.

### Validation snapshot (2026-03-20)
- `npm run lint` — passed.
- `npm run typecheck` — passed.
- `npx playwright test` — **11/11 passed** (both `cached-browse.spec.ts` and `refresh-path.spec.ts`).
- Backend: `test_refresh_processing` **12/12 passed**. `test_api_smoke` 29, `test_config` 4, `test_manual_integration_evidence` 14 — all passed. Total: **59 backend tests**.

### Branch and worktree state
- **Active branch:** `v3.0` (5 commits ahead of `master`).
- Working tree is **clean**. Branch is **up to date** with `origin/v3.0`.
- `master` remains at the Phase 6→7 gate (commit `8b54903`).
- No open PRs or issues (verified 2026-03-20; GitHub CLI unavailable 2026-03-21 due to TLS cert issue).
- Legacy remote-only branches remain: `v1.1`, `v1.2`, `v1.3`, `v1.4`. Kept for historical reference.

### v3.0 commits (not yet on master)
```
2501624 Update specs for country support, banner images, and new components
f87e332 Update About modal version to v3.0.0 and fix premature license claim
2f240b2 Tighten country param validation and include country in normalization
4c43e0f Fix skeleton loading to show image placeholders on all cards
b10a31c Add country support, banner images, About modal
```

### Open review findings

**[P2] Spec version naming drift.** About modal shows v3.0.0. Branch is named `v3.0`. But specs (`OVERVIEW.md`, `FRONTEND.md`, `BACKEND.md`) still reference "v2" throughout. Decision needed: formally adopt v3.0 naming across all specs, or treat the About modal version as the display version while specs remain product-version-agnostic.

**[P3] OVERVIEW.md architecture diagram stale.** Diagram shows only `country=us` in the NewsAPI box. Should reflect dual `country=us` and `country=gb` fetch since that's now shipped.

**[P3] `package.json` version placeholder.** Frontend `package.json` still shows `"version": "0.1.0"`. Not blocking, but inconsistent with the v3.0.0 displayed in the About modal.

**[P3] Accessibility gaps.** Foundation is good (aria-labels, prefers-reduced-motion in CSS, focus-visible utilities). Remaining gaps:
- `CountryFilter` and `SourceFilter` lack aria-labels
- No `aria-live` regions for dynamic content updates
- No `<nav>` landmark for filter controls
- No `aria-busy` on refresh button during processing
- ShadCN Dialog components provide focus trapping, but not explicitly verified

## 2. Active phase

**Phase 7 — Feature buildout + spec alignment.** Country support and About modal are shipped on `v3.0`. Remaining Phase 7 items: content guardrails, accessibility pass, topic filtering UI. Spec version alignment is a prerequisite for the open-source launch in Phase 8.

## 3. Ordered checklist

### Completed (Phase 5)
- [x] Full source verification (5 passes): zero code-spec mismatches.
- [x] Test isolation fix in `test_refresh_processing.py`.
- [x] PR #4 security dependency bump — merged 2026-03-20.
- [x] Spec alignment: `FRONTEND.md` version string, project structure; `ROADMAP.md` loop order; validation command docs.
- [x] GitHub repo description updated to v2 language.
- [x] Playwright e2e — 11/11 passed.
- [x] Package-lock.json committed.
- [x] PR #5: merge `v2.0-UX` → `master` — merged 2026-03-20.
- [x] Branch cleanup: deleted local+remote `v2.0`, `v2.0-Codex`, `v2.0-Security`, `v2.0-UX`.

### Completed (Phase 6 — UX polish)
- [x] Evaluate headline rewrite visibility. No display bug; added `_validate_result` normalization + 3 tests.
- [x] Upgrade article card layout. Full-width 16:9 banner images, sentiment badges, image error fallback.
- [x] Header/feed layout alignment. `max-w-3xl` on header container.
- [x] Evaluate broader roadmap items. Assessment complete — see roadmap table below.

### Completed (Phase 7 — partial)
- [x] **Country-aware reading.** `country` column, dual US+GB fetch, frontend CountryFilter, country badges. DB migration for legacy databases.
- [x] **About modal.** `about-modal.tsx` with ShadCN Dialog. About button in header. App explanation, how-it-works list, GitHub link, Buy Me a Coffee link, v3.0.0/attribution footer.

### Active (Phase 7 — remaining)

- [ ] [P2] **Spec version alignment.** Update `specs/OVERVIEW.md`, `specs/FRONTEND.md`, `specs/BACKEND.md` to reflect v3.0 naming. Update OVERVIEW.md architecture diagram for dual US+GB fetch. Update GitHub repo description if still referencing v2.
- [ ] [P2] **Content guardrails.** Add keyword-based exclusions for war, suicide, depression, death, and grief to `good_news.py`. Expand `apply_good_news_rules()` and `good_news_filter_expression()`. Update frontend toggle hint. Add tests for new exclusions.
- [ ] [P2] **Merge v3.0 → master.** Create PR once spec alignment and content guardrails are complete. Run full validation suite before merge.
- [ ] [P3] **Accessibility pass.** Add aria-labels to CountryFilter and SourceFilter. Add `<nav>` landmark for filter bar. Add `aria-live` region for article count updates. Add `aria-busy` to refresh button during processing. Verify modal focus trapping. Test keyboard navigation through all controls.
- [ ] [P3] **Topic filtering UI.** Add `/api/categories` endpoint returning category names and counts. Create `CategoryFilter` component (pattern matches `SourceFilter`). Wire into page state and URL query params.

### Roadmap evaluation results (Phase 6 → Phase 7 gate)

| Item | Status | Notes |
|------|--------|-------|
| Country-aware reading | **SHIPPED** | Dual US+GB fetch, frontend filter, country badges |
| About modal | **SHIPPED** | v3.0.0 with GitHub + Buy Me a Coffee links |
| Content guardrails | **Active** | Expand good_news.py for war/suicide/depression/death/grief |
| Accessibility pass | **Active** | Good foundation; gaps in aria-labels, landmarks, live regions |
| Topic filtering UI | **Active** | Backend category param exists; need `/api/categories` endpoint + frontend component |
| Processing visibility | **Deferred** | Heaviest lift; best done after simpler features prove UX patterns |
| Fact Checker Mode | **Deferred** | Depends on topic infrastructure; evolved into Article Comparison for Phase 8 |

### Planned (Phase 8 — Open source launch + Article Comparison)

**Open source packaging:**
- [ ] [P2] **AGPLv3 LICENSE file.** Add to repo root. Update `package.json` license field.
- [ ] [P2] **README overhaul.** Rewrite for open-source audience: hero section, quick-start guide (< 5 min), personalisation section, Claude prompt template for customising preferences/triggers, architecture overview, premium API note, contributing guidelines with CLA mention.
- [ ] [P3] **Demo video.** Screen recording with OBS, edit with DaVinci Resolve, upload to YouTube, link from README and About modal.

**Article Comparison feature:**
- [ ] [P3] **Article Comparison.** New `/comparison` page showing how the same story is framed differently across sources/countries. Backend: `GET /api/comparison` (fuzzy title matching), `POST /api/comparison/analyse` (one AI call per group). Frontend: side-by-side card layout with AI analysis panel. Test with 2 article groups.

**Future considerations:**
- [ ] [P4] **Pluggable news source architecture.** Abstract NewsAPI so alternatives can be swapped in.
- [ ] [P4] **User-configurable content guardrails.** Let users specify trigger words and topics to avoid.

## 4. Notes / discoveries that matter for the next loop

- **Version naming decision needed.** The v3.0 branch and About modal use v3.0.0 but specs still say "v2". Recommendation: update specs to v3.0 since the branch name, About modal, and major new features (country support, banner images) justify the version bump.
- **GitHub CLI unavailable.** TLS cert verification failing as of 2026-03-21. PR creation and issue checks will need retrying later or using the web UI.
- **SOCKS proxy test isolation.** The `AIService.__init__` mock fix prevents `OpenAI()` client setup from leaking. Root cause is environment proxy variables, not a missing dependency.
- **Test count.** 59 backend tests across 4 test modules. 11 Playwright e2e tests.
- **Frontend helper tests** use `node --test --experimental-strip-types`. Experimental warnings are expected.
- **Manual evidence helper** intentionally leaves human-fill TODO placeholders by design.
- **Code-spec alignment is strong** for shipped features. Only drift is version naming (v2 in specs vs v3.0 in runtime).
- **Dual US+GB fetch doubles API usage** from ~7 to ~14 requests per refresh. Within 100/day free limit (~7 refreshes/day).
- **`package.json` version** (`0.1.0`) doesn't match displayed version (`v3.0.0`). Low priority but should align before open-source launch.

## 5. Next recommended build slice

**Spec version alignment** — then **content guardrails** — then **v3.0 → master merge**.

Spec version alignment first (small, low-risk, unblocks everything else):
1. Update `specs/OVERVIEW.md`: change "v2.0" references to "v3.0", update architecture diagram to show dual `country=us,gb` fetch.
2. Update `specs/FRONTEND.md`: change "v2 frontend" to "v3 frontend", verify project structure listing is current.
3. Update `specs/BACKEND.md`: change "v2" references to "v3" where applicable, verify all columns and endpoints match.
4. Update GitHub repo description to reference v3 (if GitHub CLI becomes available).
5. Commit spec updates.

Then content guardrails:
1. Add keyword tuples for war, suicide, depression, death, grief in `good_news.py`.
2. Create helper functions matching the `is_politics_story()` pattern.
3. Update `apply_good_news_rules()` to apply the new exclusions.
4. Update `good_news_filter_expression()` SQL filter to include new keyword checks.
5. Update frontend `good-news-toggle.tsx` hint text to reflect expanded exclusions.
6. Add unit tests for each new exclusion category.
7. Update `specs/BACKEND.md` and `specs/ROADMAP.md` to reflect shipped guardrails.

Then v3.0 → master merge:
1. Run full validation: backend tests, lint, typecheck, Playwright e2e.
2. Create PR with summary of all v3.0 changes.
3. Merge after CI passes.
