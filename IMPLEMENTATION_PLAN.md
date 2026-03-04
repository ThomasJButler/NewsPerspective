# Implementation Plan -- NewsPerspective v2.0

> **Status**: Phases 1-2 functionally complete (Steps 1-14). Quality defects found in code audit. Phase 2.5 (Quality Fixes) added before Phase 3 (Integration and Polish).

---

## Spec Gaps — All Resolved

All 12 spec gaps identified at planning time have been resolved in the implementation. See inline notes on the completed steps below.

---

## Phase 1: Backend Foundation — COMPLETE

All backend work lives in `src/backend/`. All steps functional.

- [x] **Step 1: Project scaffolding + configuration**
- [x] **Step 2: AI service**
- [x] **Step 3: News fetcher**
- [x] **Step 4: Article processor**
- [x] **Step 5: Pydantic schemas**
- [x] **Step 6: API routers**
- [x] **Step 7: FastAPI app assembly**
- [x] **Step 8: Backend verification**

---

## Phase 2: Frontend — COMPLETE

All frontend work lives in `src/frontend/`. All steps functional.

- [x] **Step 9: Next.js + ShadCN scaffolding**
- [x] **Step 10: TypeScript types + API client + utilities + hooks**
- [x] **Step 11: Core UI components**
- [x] **Step 12: Home page**
- [x] **Step 13: Article detail page**
- [x] **Step 14: Dark mode**

---

## Phase 2.5: Quality Fixes (Pre-Integration)

Code audit of completed Steps 1-14 revealed defects that should be fixed before integration testing. Ordered by priority.

- [ ] **Step QF-1: Typography — fix broken font configuration** *(HIGH — visible to every user)*
  - **Problem**: `globals.css` references `var(--font-geist-sans)` and `var(--font-geist-mono)` but `layout.tsx` does not import Geist fonts. CSS variables are unset, so text falls back to browser default sans-serif. The spec explicitly says "NOT Inter" and wants "distinctive but clean font pairing" — headlines are the product.
  - **Fix**: Choose a font strategy:
    - Option A: Import Geist Sans + Geist Mono via `next/font/google` (or local) in `layout.tsx`, apply CSS variables to `<body>`.
    - Option B: Replace with a different pairing per the spec's "distinctive" requirement (e.g., a serif for headlines + clean sans for body).
  - **Files**: `src/frontend/app/layout.tsx`, `src/frontend/app/globals.css`

- [ ] **Step QF-2: Settings dialog — replace custom modal with ShadCN Dialog** *(HIGH — accessibility violation)*
  - **Problem**: `settings-dialog.tsx` is a hand-rolled modal using a fixed backdrop div. It has `role="dialog"`, `aria-modal`, and ESC-to-close, but **lacks focus trap** — keyboard users can tab outside the open dialog. The implementation plan (Step 11) specifies "ShadCN Dialog... proper focus trap, ESC to close, ARIA labels."
  - **Fix**: Replace the custom implementation with ShadCN's Dialog component (which wraps Radix Dialog and provides focus trap, scroll lock, and portal automatically). Note: `@radix-ui/react-dialog` is already in `package-lock.json` as a transitive dependency.
  - **Files**: `src/frontend/components/settings-dialog.tsx`
  - Add ShadCN Dialog component: `npx shadcn@latest add dialog`

- [ ] **Step QF-3: Error handling UI — surface API errors to users** *(HIGH — silent failures)*
  - **Problem**: All `catch` blocks in `page.tsx` are empty (`catch(() => {})`). When the backend is unreachable, the API key is invalid (401), or the refresh fails, the user sees nothing — no toast, no alert, no error state. The refresh button just stops spinning silently.
  - **Fix**: Add a minimal error feedback mechanism. Options:
    - Option A: ShadCN Toast/Sonner for transient errors (recommended — lightweight)
    - Option B: Inline error banners above the article feed
  - At minimum, surface: refresh failures (especially 401 "invalid API key"), network errors on article fetch, and article-not-found on detail page.
  - **Files**: `src/frontend/app/page.tsx`, `src/frontend/app/article/[id]/page.tsx`, possibly new toast component

- [ ] **Step QF-4: Fix `.env.template` — remove stale `NEWS_API_KEY`** *(MEDIUM — confusing for new developers)*
  - **Problem**: `.env.template` still lists `NEWS_API_KEY=your_newsapi_key_here` as the first entry. In v2, the News API key is user-provided via the frontend — there is no server-side `NEWS_API_KEY`. This misleads developers into thinking they need to set it.
  - **Fix**: Remove the `NEWS_API_KEY` line from `.env.template`. Add a comment explaining the user-provided key model.
  - **Files**: `.env.template`

- [ ] **Step QF-5: Backend — instantiate AIService once per batch** *(MEDIUM — performance)*
  - **Problem**: In `article_processor.py`, `AIService()` is instantiated inside the per-article loop (line ~55). This creates a new `AzureOpenAI` client object for every single article. While functional, it is wasteful — the client should be reused.
  - **Fix**: Move `AIService()` instantiation to `ArticleProcessor.__init__()` or to the top of `process_new_articles()`, before the article loop.
  - **Files**: `src/backend/services/article_processor.py`

- [ ] **Step QF-6: Backend — parse `published_at` datetime explicitly** *(LOW — fragile coercion)*
  - **Problem**: In `article_processor.py`, `raw.get("published_at")` returns an ISO 8601 string from NewsAPI. This string is assigned directly to a SQLAlchemy `DateTime` column. SQLAlchemy's implicit coercion handles it, but this is fragile and will break with unexpected date formats.
  - **Fix**: Add explicit `datetime.fromisoformat()` parsing (with a try/except fallback to `None`) when setting `published_at` on the Article model.
  - **Files**: `src/backend/services/article_processor.py`

- [ ] **Step QF-7: Remove dead code** *(LOW — cleanup)*
  - `NewsFetcher.fetch_everything()` in `src/backend/services/news_fetcher.py` — method exists but is never called anywhere in the codebase.
  - `truncateText()` in `src/frontend/lib/utils.ts` — function exists but is never called.
  - **Fix**: Remove both. (If `fetch_everything` is wanted for future use, it can be re-added then.)

---

## Phase 3: Integration and Polish

- [ ] **Step 15: End-to-end integration testing**
  - Start both backend (`uvicorn`) and frontend (`npm run dev`) simultaneously
  - `POST /api/refresh` with `X-News-Api-Key` header to trigger article processing
  - Verify articles render in the frontend with rewritten headlines and TLDR summaries
  - Test Good News toggle filters to only `is_good_news` articles
  - Test source filter dropdown populates and filters correctly
  - Test search bar filters by headline text with debounce
  - Test article detail page navigation and rendering
  - Test dark mode toggle in both light and dark themes
  - Test "Load More" pagination
  - Test empty states (no articles, no search results)
  - Test error states: backend unreachable, invalid API key on refresh (should show toast/error from QF-3)
  - Test API key flow: onboarding setup, settings dialog change/remove key
  - Verify keyboard navigation through all interactive elements
  - Fix any issues discovered
  - **Dependencies**: Phase 2.5 complete

- [ ] **Step 16: Developer experience**
  - Root `Makefile` with targets:
    - `dev` -- start both backend and frontend concurrently
    - `backend` -- start backend only
    - `frontend` -- start frontend only
    - `install` -- install both Python and Node dependencies
  - Create `src/backend/requirements.txt` with all Python dependencies (fastapi, uvicorn, sqlalchemy, pydantic-settings, openai, requests, python-dotenv)
  - Update `CLAUDE.md` with v2.0 commands (replace v1 references)
  - Update `AGENTS.md`: remove stale `NEWS_API_KEY` reference, document user-provided key model, update curl examples to include `X-News-Api-Key` header
  - **Dependencies**: Step 15

- [ ] **Step 17: Legacy cleanup**
  - Move legacy v1 files to `legacy/` directory: `run.py`, `batch_processor.py`, `azure_ai_language.py`, `azure_document_intelligence.py`, `web_app.py`, `search.py`, `logger_config.py`, `loop.sh`
  - Move `rewrites.png` to `legacy/`
  - Update `README.md` for v2.0 (new architecture, new setup instructions)
  - Final `.gitignore` review
  - **Dependencies**: Step 16

---

## Implementation Order Summary

| Priority | Step | Description | Status |
|----------|------|-------------|--------|
| 1-8 | Steps 1-8 | Backend Foundation | DONE |
| 9-14 | Steps 9-14 | Frontend | DONE |
| **15** | **QF-1** | **Fix broken font configuration** | TODO |
| **16** | **QF-2** | **Settings dialog → ShadCN Dialog (focus trap)** | TODO |
| **17** | **QF-3** | **Error handling UI (surface API errors)** | TODO |
| **18** | **QF-4** | **Fix .env.template (remove NEWS_API_KEY)** | TODO |
| **19** | **QF-5** | **AIService instantiation (once per batch)** | TODO |
| **20** | **QF-6** | **Parse published_at datetime explicitly** | TODO |
| **21** | **QF-7** | **Remove dead code** | TODO |
| 22 | Step 15 | End-to-end integration testing | TODO |
| 23 | Step 16 | Developer experience | TODO |
| 24 | Step 17 | Legacy cleanup | TODO |

**Parallelism note**: QF-1 through QF-7 are all independent and can be implemented in parallel. Steps 15-17 must be sequential.
