# IMPLEMENTATION_PLAN.md

## 1. Current status summary and code review

Updated on 2026-03-21 (tenth pass, Claude Code Opus 4.6, `v3.0` branch).

### Verified runtime state
- `POST /api/refresh` requires a user-supplied `X-News-Api-Key`. The backend does not read a server-side `NEWS_API_KEY`.
- Cached read-only endpoints work without a key.
- `src/backend/services/article_processor.py` does one AI call per new article and stores sentiment, rewrite output, TLDR, and Good News state together.
- Good News exclusions for `sports`, `entertainment`, and detected `politics` are enforced in backend logic (`utils/good_news.py`) and reflected in frontend behavior.
- Country support is end-to-end: `country` column in DB (`models.py:49`) with migration (`main.py:25-31`), dual US+GB fetch in `news_fetcher.py`, `Literal["us", "gb"]` country query param on `GET /api/articles` (`articles.py:45`), `CountryFilter` component in frontend, country badges on article cards.
- About modal (`about-modal.tsx`) shows v3.0.0, explains the app, includes GitHub and Buy Me a Coffee links, shows "AGPLv3".
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
- Good-news toggle hint text updated to: "Excludes sports, entertainment, politics, and distressing content." (`good-news-toggle.tsx:34`).

### Validation snapshot (2026-03-21, post-comparison endpoint)
- `npm run lint` — passed.
- `npm run typecheck` — passed.
- `npx playwright test` — **11/11 passed** (run 2026-03-21). Fixed 4 broken tests: updated good-news hint text assertion to match new guardrails copy, and disambiguated `getByRole("combobox")` selectors to `getByRole("combobox", { name: "Filter by source" })` since CountryFilter and CategoryFilter added two more comboboxes.
- Backend: all 5 test modules run together — **78/78 passed** (`test_api_smoke` 35, `test_refresh_processing` 13, `test_manual_integration_evidence` 14, `test_config` 4, `test_comparison` 12).

### Branch and worktree state
- **Active branch:** `v3.0` (8 commits ahead of `master`).
- Working tree is **clean**. Branch is **up to date** with `origin/v3.0`.
- `master` remains at the Phase 6→7 gate (commit `8b54903`).
- **PR created:** v3.0 → master merge PR opened (pending — GitHub CLI TLS cert issue persists; MCP GitHub tool used instead).
- Legacy remote-only branches remain: `v1.1`, `v1.2`, `v1.3`, `v1.4`. Kept for historical reference.

### v3.0 commits (not yet on master)
```
ce17dd1 Implementation plan v3.0 and Claude flag update
2501624 Update specs for country support, banner images, and new components
f87e332 Update About modal version to v3.0.0 and fix premature license claim
2f240b2 Tighten country param validation and include country in normalization
4c43e0f Fix skeleton loading to show image placeholders on all cards
b10a31c Add country support, banner images, About modal
```

### Open review findings

**[RESOLVED] Spec version naming drift.** All specs, `AGENTS.md`, `CLAUDE.md`, and `package.json` now use v3.0 naming consistently. Remaining intentional "v2" references: NewsAPI `/v2/top-headlines` URL path (external API), historical "What Changed From v1" section in `OVERVIEW.md`, and completed-task history in `IMPLEMENTATION_PLAN.md`.

**[RESOLVED] Content guardrails.** Shipped in both the normal feed and Good News mode, matching `specs/ROADMAP.md` intent. Keyword-based exclusion for war, suicide, depression, death, and grief topics applied at query time in `articles.py` and `good_news_filter_expression`. Stories remain in the database for audit but are hidden from browse results. 4 new tests cover processing-level and API-level guardrail behavior.

**[RESOLVED] OVERVIEW.md architecture diagram.** Updated to show dual `country=us, country=gb` fetch.

**[RESOLVED] `package.json` version.** Updated from `0.1.0` to `3.0.0`.

**[RESOLVED] Accessibility gaps.** All identified gaps addressed: `aria-label` on `CountryFilter` and `SourceFilter` select triggers, `<nav>` landmark wrapping filter bar, `aria-live="polite"` on stats bar, `aria-busy` on refresh button, ShadCN Dialog focus trapping verified (Radix UI built-in). Remaining foundation: aria-labels on refresh/settings/about buttons, `aria-describedby` on good-news toggle, `prefers-reduced-motion` in CSS, `focus-visible` utilities.

**[RESOLVED] No `/api/categories` endpoint.** Shipped `GET /api/categories` returning `{categories: [{name, count}]}` from processed articles. Frontend `CategoryFilter` component wired into page state and URL query params.

## 2. Active phase

**Phase 7 — Feature buildout + spec alignment.** Country support and About modal are shipped on `v3.0`. Remaining Phase 7 items: spec version alignment, content guardrails (scope decision required), accessibility pass, topic filtering UI. Spec version alignment is a prerequisite for the open-source launch in Phase 8.

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

- [x] [P2] **Spec version alignment.** Updated `specs/OVERVIEW.md`, `specs/FRONTEND.md`, `specs/BACKEND.md`, `specs/ROADMAP.md` to reflect v3.0 naming. Updated `OVERVIEW.md` architecture diagram for dual US+GB fetch. Updated `AGENTS.md` and `CLAUDE.md` purpose line and product rules from "v2" to "v3". Updated `package.json` version to `3.0.0`. GitHub repo description update deferred until CLI becomes available.
- [x] [P2] **Content guardrails.** Keyword-based exclusion for war, suicide, depression, death, grief. Applied to both normal feed (`articles.py` base query) and Good News mode (`good_news_filter_expression`). Processing-time `apply_good_news_rules` also updated. Frontend hint text updated. Specs updated (`BACKEND.md`, `ROADMAP.md`). 4 new tests (1 processing + 3 API). Total: 63 backend tests.
- [x] [P2] **Merge v3.0 → master.** PR created. Full validation passed: 63/63 backend tests, lint clean, typecheck clean. Playwright 11/11 on last code-affecting commit. Awaiting merge.
- [x] [P3] **Accessibility pass.** Added `aria-label` to `CountryFilter` and `SourceFilter` `SelectTrigger` elements. Wrapped filter bar in `<nav aria-label="Article filters">` landmark. Added `aria-live="polite"` on `StatsBar` for article count announcements. Added `aria-busy` to refresh button during processing. Verified ShadCN Dialog focus trapping (Radix UI primitive provides built-in focus trap, Escape dismiss, and focus return).
- [x] [P3] **Topic filtering UI.** Added `GET /api/categories` endpoint returning `{categories: [{name, count}]}` from processed articles. Created `CategoryFilter` component (pattern matches `SourceFilter`). Wired into page state and URL query params. Backend schemas: `CategoryItem`, `CategoriesResponse`. Frontend types, API client, component, and page wiring all complete. 3 new backend tests. Total: 66 backend tests.

### Roadmap evaluation results (Phase 6 → Phase 7 gate)

| Item | Status | Notes |
|------|--------|-------|
| Country-aware reading | **SHIPPED** | Dual US+GB fetch, frontend filter, country badges |
| About modal | **SHIPPED** | v3.0.0 with GitHub + Buy Me a Coffee links |
| Content guardrails | **SHIPPED** | Keyword exclusion for war/suicide/depression/death/grief in both feeds |
| Accessibility pass | **SHIPPED** | aria-labels, landmarks, live regions, aria-busy on refresh |
| Topic filtering UI | **SHIPPED** | `GET /api/categories` endpoint + `CategoryFilter` component + URL sync |
| Processing visibility | **Deferred** | Heaviest lift; best done after simpler features prove UX patterns |
| Fact Checker Mode | **Deferred** | Depends on topic infrastructure; evolved into Article Comparison for Phase 8 |

### Planned (Phase 8 — Open source launch + Article Comparison)

**Open source packaging:**
- [x] [P2] **AGPLv3 LICENSE file.** Added canonical AGPLv3 text to repo root `LICENSE`. Updated `package.json` license field to `"AGPL-3.0-only"`. Updated About modal from "Coming soon" to "AGPLv3". Also fixed broken GitHub URL (`tombutler` -> `ThomasJButler`) and Buy Me a Coffee URL in About modal.
- [x] [P2] **README overhaul.** Rewrote for open-source audience: hero section with tagline, quick-start guide (5 steps), personalisation section with Claude prompt template, architecture diagram, NewsAPI free tier note with premium mention, contributing guidelines with CLA mention, Docker section, development/validation section. Also cleaned up stale `specs/ROADMAP.md` sections (marked shipped features, updated Fact Checker → Article Comparison, trimmed stale loop order).
- [ ] [P3] **Demo video.** Screen recording with OBS, edit with DaVinci Resolve, upload to YouTube, link from README and About modal.

**Article Comparison feature:**
- [x] [P3] **Article Comparison — backend grouping endpoint.** `GET /api/comparison` with fuzzy title matching (Jaccard similarity on normalized word sets). Returns groups of 2+ related articles with representative title, article summaries, sources, and countries. New files: `utils/title_similarity.py`, `routers/comparison.py`. Schemas: `ComparisonArticleSummary`, `ComparisonGroup`, `ComparisonResponse`. 12 new tests (8 unit + 3 integration + 1 field check). Content guardrails applied to comparison results.
- [ ] [P3] **Article Comparison — AI analysis endpoint.** `POST /api/comparison/analyse` accepting a group of article IDs, running one AI call per group to produce a framing analysis. Schema: `ComparisonAnalysis`. Test with mocked AI response.
- [ ] [P3] **Article Comparison — frontend page.** New `/comparison` page with side-by-side card layout and AI analysis panel. Navigation link from header. Spec updates for new route and components.

**Future considerations:**
- [ ] [P4] **Pluggable news source architecture.** Abstract NewsAPI so alternatives can be swapped in.
- [ ] [P4] **User-configurable content guardrails.** Let users specify trigger words and topics to avoid.

## 4. Notes / discoveries that matter for the next loop

- **Content guardrails shipped.** Applied to both normal feed and Good News mode per `specs/ROADMAP.md`. Keyword-based query-time exclusion in `articles.py` and `good_news_filter_expression`. Stories remain stored but hidden from browse.
- **Version naming aligned.** All specs, `AGENTS.md`, `CLAUDE.md`, and `package.json` now consistently use v3.0 naming.
- **GitHub CLI unavailable.** TLS cert verification failing as of 2026-03-21. PR creation and issue checks will need retrying later or using the web UI.
- **Validation current.** Full backend+frontend validation re-run 2026-03-21 against HEAD (`1e4f5cd`). All 63 backend tests, lint, and typecheck passed. Playwright not re-run due to sandbox port restriction but last passing run covers all code-affecting commits.
- **SOCKS proxy test isolation.** The `AIService.__init__` mock fix prevents `OpenAI()` client setup from leaking. Root cause is environment proxy variables, not a missing dependency.
- **Test count.** 78 backend tests across 5 test modules. 11 Playwright e2e tests.
- **Frontend helper tests** use `node --test --experimental-strip-types`. Experimental warnings are expected.
- **Manual evidence helper** intentionally leaves human-fill TODO placeholders by design.
- **Code-spec alignment is strong** for shipped features. Version naming is now consistent across all specs and runtime.
- **specs/ROADMAP.md cleaned up.** Shipped features (country filter, category filter, visual refinements, headline rewrite visibility, about modal, accessibility pass) now marked as shipped. Stale near-term loop order removed. Fact Checker Mode replaced with Article Comparison (Planned).
- **Dual US+GB fetch doubles API usage** from ~7 to ~14 requests per refresh. Within 100/day free limit (~7 refreshes/day).
- **`package.json` version** now `3.0.0`, matching the About modal display version.

## 5. Next recommended build slice

**Article Comparison — AI analysis endpoint [P3]** — `POST /api/comparison/analyse` accepting a group of article IDs, running one AI call per group to produce a framing analysis comparing how different sources/countries cover the same story. After that: frontend `/comparison` page. Demo video [P3] is a human task (OBS recording + DaVinci Resolve edit + YouTube upload) and can be done in parallel.
