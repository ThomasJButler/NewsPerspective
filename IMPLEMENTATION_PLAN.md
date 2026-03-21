# IMPLEMENTATION_PLAN.md

## 1. Current status summary and code review

Updated on 2026-03-21 (fifteenth pass, Claude Code Opus 4.6, `v3.0` branch).

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
- No TODO/FIXME/HACK markers in production code (backend or frontend). Manual evidence helper TODOs are intentional placeholders.
- Backend article model schema matches `specs/BACKEND.md` persistence model exactly.
- Frontend proxy (`next.config.ts`) rewrites `/api/*` to `BACKEND_ORIGIN` (default `http://localhost:8000`), matching spec.
- All frontend components, hooks, types, and library files documented in `specs/FRONTEND.md` exist in the tree.
- `specs/AI_PROMPTS.md` system prompt and user prompt template match actual strings in `src/backend/services/ai_service.py` exactly. No drift.
- Next.js version in `package.json` is `16.1.7`, matching `specs/FRONTEND.md`.
- Good-news toggle hint text: "Excludes sports, entertainment, politics, and distressing content." (`good-news-toggle.tsx:34`).
- Article Comparison fully shipped: `GET /api/comparison`, `POST /api/comparison/analyse`, frontend `/comparison` route.
- Pluggable `NewsSource` protocol shipped with DI in `ArticleProcessor`.
- User-configurable content guardrails shipped: `GET/PUT /api/settings/guardrails`, frontend "Blocked topics" in settings dialog.
- Content guardrails enforced consistently across all read endpoints: article list, single-article, categories, sources, and stats.

### Validation snapshot (2026-03-21, fifteenth pass)
- `npm run lint` — passed.
- `npm run typecheck` — passed.
- `npx playwright test` — **11/11 passed** (run 2026-03-21).
- Backend: **108 tests across 6 modules** (`test_api_smoke` 35, `test_refresh_processing` 13, `test_manual_integration_evidence` 14, `test_config` 4, `test_comparison` 21, `test_custom_guardrails` 21). All pass both per-module and in a single unified run.

### Branch and worktree state
- **Active branch:** `v3.0` (**22 commits** ahead of `master`).
- `master` remains at the Phase 6→7 gate (commit `8b54903`).
- **PR #6 is open** (v3.0 → master). Confirmed via GitHub API. Ready to merge after push.
- Legacy remote-only branches remain: `v1.1`, `v1.2`, `v1.3`, `v1.4`. Kept for historical reference.

### v3.0 commits (not yet on master)
```
d90370a Add user-configurable content guardrails frontend
c3ab0cf Add user-configurable content guardrails backend
26bffa8 Add pluggable NewsSource protocol with dependency injection
779f586 Add /comparison page with side-by-side article groups and AI analysis
df2df84 Add POST /api/comparison/analyse endpoint with AI framing analysis
016b2c5 Add GET /api/comparison endpoint with fuzzy title grouping
f5f7d68 Add AGPLv3 LICENSE, fix about-modal URLs, update e2e test selectors
ea88844 Rewrite README for open-source audience and clean up stale ROADMAP sections
7d03b5f Wire CategoryFilter into page state, URL params, and metadata loading
2aba547 Create category-filter.tsx
3d2a4f8 Add ARIA attributes to improve accessibility
3b5c72b Add accessibility improvements: aria-labels, nav landmark, live region, aria-busy
dc41059 Update plan for v3.0 → master PR and fresh validation run
1e4f5cd Add content guardrails for war, suicide, depression, death, and grief
9b37e29 Align all specs, docs, and package.json to v3.0 naming
ce17dd1 Implementation plan v3.0 and Claude flag update
2501624 Update specs for country support, banner images, and new components
f87e332 Update About modal version to v3.0.0 and fix premature license claim
2f240b2 Tighten country param validation and include country in normalization
4c43e0f Fix skeleton loading to show image placeholders on all cards
b10a31c Add country support, banner images, About modal
```

### Open review findings

**[RESOLVED] Spec text drift — shipped features described as future/planned.** Fixed in all three spec files. Content guardrails and Article Comparison now described as shipped.

**[RESOLVED] README test count and module list stale.** Updated to 98 tests across 6 modules with `test_comparison` and `test_custom_guardrails` added.

**[RESOLVED] Validation commands missing `test_comparison`.** Added to both `CLAUDE.md` and `AGENTS.md`.

**[RESOLVED] Spec version naming drift.** All specs, `AGENTS.md`, `CLAUDE.md`, and `package.json` now use v3.0 naming consistently. Remaining intentional "v2" references: NewsAPI `/v2/top-headlines` URL path (external API), historical "What Changed From v1" section in `OVERVIEW.md`, and completed-task history in `IMPLEMENTATION_PLAN.md`.

**[RESOLVED] Content guardrails.** Shipped in both the normal feed and Good News mode, matching `specs/ROADMAP.md` intent.

**[RESOLVED] OVERVIEW.md architecture diagram.** Updated to show dual `country=us, country=gb` fetch.

**[RESOLVED] `package.json` version.** Updated from `0.1.0` to `3.0.0`.

**[RESOLVED] Accessibility gaps.** Core gaps addressed. Remaining foundation: `aria-describedby` on good-news toggle, `prefers-reduced-motion` in CSS, `focus-visible` utilities.

**[RESOLVED] No `/api/categories` endpoint.** Shipped.

**[RESOLVED] Inconsistent guardrail enforcement across read endpoints (CodeRabbit PR #6).** Single-article, categories, sources, and stats endpoints now apply both built-in and custom content guardrails. 10 new tests added. 108/108 pass unified.

## 2. Active phase

**Phase 9 — Documentation alignment + developer experience.** Phases 7 and 8 are complete (all checklist items shipped). The remaining work is documentation alignment to make specs, README, and validation commands match the actual shipped state, plus the v3.0 → master merge and demo video.

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
- [x] Evaluate headline rewrite visibility. Added `_validate_result` normalization + 3 tests.
- [x] Upgrade article card layout. Full-width 16:9 banner images, sentiment badges, image error fallback.
- [x] Header/feed layout alignment. `max-w-3xl` on header container.
- [x] Evaluate broader roadmap items. Assessment complete.

### Completed (Phase 7 — Feature buildout + spec alignment)
- [x] Country-aware reading. Dual US+GB fetch, frontend CountryFilter, country badges, DB migration.
- [x] About modal. v3.0.0 with GitHub + Buy Me a Coffee links, AGPLv3 license.
- [x] Spec version alignment. All specs, `AGENTS.md`, `CLAUDE.md`, `package.json` updated to v3.0.
- [x] Content guardrails. Keyword exclusion for war/suicide/depression/death/grief in both feeds.
- [x] Accessibility pass. aria-labels, landmarks, live regions, aria-busy on refresh.
- [x] Topic filtering UI. `GET /api/categories` + `CategoryFilter` component + URL sync.

### Completed (Phase 8 — Open source launch + Article Comparison)
- [x] AGPLv3 LICENSE file. Canonical text, `package.json` license field, About modal updated.
- [x] README overhaul. Open-source audience, quick-start, architecture diagram, NewsAPI free tier note, contributing guidelines.
- [x] Article Comparison — backend grouping. `GET /api/comparison` with Jaccard similarity. 12 tests.
- [x] Article Comparison — AI analysis. `POST /api/comparison/analyse` with framing analysis. 9 tests.
- [x] Article Comparison — frontend page. `/comparison` route with side-by-side view and AI analysis.
- [x] Pluggable news source architecture. `NewsSource` protocol, DI in `ArticleProcessor`.
- [x] User-configurable content guardrails — backend. `Setting` model, `GET/PUT /api/settings/guardrails`, 11 tests.
- [x] User-configurable content guardrails — frontend. "Blocked topics" in settings dialog.

### Active (Phase 9 — Documentation alignment + DX)

- [x] [P1] **Fix spec text drift — remove "future work" claims for shipped features.** Updated `specs/OVERVIEW.md:11,59`, `specs/FRONTEND.md:76`, and `specs/ROADMAP.md:85,89` to reflect that content guardrails and Article Comparison are shipped.
- [x] [P1] **Update validation commands.** Added `python -m unittest src.backend.tests.test_comparison -v` to `CLAUDE.md` and `AGENTS.md` validation sections.
- [x] [P2] **Update README test count.** Changed `README.md` from "66 tests across 4 modules" to "98 tests across 6 modules" and added `test_comparison` and `test_custom_guardrails` to the module list.
- [ ] [P2] **Merge v3.0 → master.** Check PR status via web UI (GitHub CLI TLS cert issue persists). Merge or recreate PR if needed. All validation passes.
- [x] [P3] **Cross-module test isolation.** Fixed: added `database.reconfigure_engine()` calls to `setUpClass` in `test_api_smoke`, `test_comparison`, and `test_custom_guardrails`. Changed `main.py` to use `database.engine` (module attribute) instead of a direct import so the lifespan function sees the reconfigured engine. All 98 tests pass in a single unified run.
- [x] [P1] **Fix inconsistent guardrail enforcement (CodeRabbit PR #6).** Applied content guardrails to `GET /api/articles/{id}`, `GET /api/categories`, `GET /api/sources`, and `GET /api/stats`. 10 new tests. 108/108 pass.
- [ ] [P3] **Demo video.** Human task: screen recording with OBS, edit with DaVinci Resolve, upload to YouTube, link from README and About modal. No code changes required.

### Roadmap evaluation results (Phase 6 → Phase 7 gate)

| Item | Status | Notes |
|------|--------|-------|
| Country-aware reading | **SHIPPED** | Dual US+GB fetch, frontend filter, country badges |
| About modal | **SHIPPED** | v3.0.0 with GitHub + Buy Me a Coffee links |
| Content guardrails | **SHIPPED** | Built-in + user-configurable keyword exclusion |
| Accessibility pass | **SHIPPED** | aria-labels, landmarks, live regions, aria-busy on refresh |
| Topic filtering UI | **SHIPPED** | `GET /api/categories` endpoint + `CategoryFilter` component + URL sync |
| Article Comparison | **SHIPPED** | Backend grouping + AI analysis + frontend `/comparison` route |
| Pluggable news sources | **SHIPPED** | `NewsSource` protocol with DI |
| User-configurable guardrails | **SHIPPED** | `GET/PUT /api/settings/guardrails` + frontend "Blocked topics" |
| Processing visibility | **Deferred** | Heaviest lift; best done after simpler features prove UX patterns |

## 4. Notes / discoveries that matter for the next loop

- **All code features and documentation alignment are complete.** The only remaining tasks (merge + demo video) are human-only.
- **[RESOLVED] Spec text drift.** All spec files updated to reflect shipped features.
- **[RESOLVED] CodeRabbit PR #6 review findings.** Inconsistent guardrail enforcement fixed across all read endpoints.
- **GitHub CLI TLS cert issue persists.** GitHub API via curl works; gh CLI does not.
- **PR #6 is open and ready.** Confirmed via GitHub API (state: open, not merged). Push latest commit then merge.
- **Validation current.** Backend 108 tests (6 modules, all pass per-module and unified), frontend lint + typecheck pass. Playwright 11/11.
- **Cross-module test isolation fixed.** All 6 modules run cleanly in a single `python -m unittest` invocation.
- **SOCKS proxy test isolation.** The `AIService.__init__` mock fix prevents `OpenAI()` client setup from leaking. Root cause is environment proxy variables.
- **Frontend helper tests** use `node --test --experimental-strip-types`. Experimental warnings are expected.
- **Manual evidence helper** intentionally leaves human-fill TODO placeholders by design.
- **Dual US+GB fetch doubles API usage** from ~7 to ~14 requests per refresh. Within 100/day free limit (~7 refreshes/day).

## 5. Next recommended build slice

**Merge v3.0 → master [P2].** PR #6 is open and confirmed via GitHub API. Push latest commit, then merge. All validation passes (108/108 unified, lint + typecheck clean).

After merge, the only remaining item is:
- **Demo video [P3]** — Screen recording with OBS, edit with DaVinci Resolve, upload to YouTube, link from README and About modal. No code changes required.
