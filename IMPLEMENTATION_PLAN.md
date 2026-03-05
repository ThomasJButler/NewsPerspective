# Implementation Plan -- NewsPerspective v2.0

> **Status**: Phases 1-2.5 complete (Steps 1-14, QF-1 through QF-7). Phase 3 (Integration and Polish) is next.

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

## Phase 2.5: Quality Fixes (Pre-Integration) — COMPLETE

- [x] **Step QF-1: Typography — fix broken font configuration**
  - Added system font stacks as fallbacks in `globals.css` for `--font-sans` and `--font-mono`. Uses `system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif` (NOT Inter). When network is available, fonts can be upgraded to Google Fonts (Plus Jakarta Sans / JetBrains Mono) via `next/font/google` in `layout.tsx`.

- [x] **Step QF-2: Settings dialog — replace custom modal with ShadCN Dialog**
  - Created `src/frontend/components/ui/dialog.tsx` using Radix Dialog from the unified `radix-ui` package. Rewrote `settings-dialog.tsx` to use the ShadCN Dialog component — now has proper focus trap, scroll lock, portal rendering, and accessible close button.

- [x] **Step QF-3: Error handling UI — surface API errors to users**
  - Created a lightweight toast notification system: `hooks/use-toast.ts` (pub/sub pattern) + `components/toaster.tsx` (renders toast list). Added `<Toaster />` to `layout.tsx`. Updated `page.tsx` to show destructive toasts on article fetch failures, refresh failures (with special 401/invalid API key messaging), and `article/[id]/page.tsx` for article detail fetch errors.

- [x] **Step QF-4: Fix `.env.template` — remove stale `NEWS_API_KEY`**
  - Removed `NEWS_API_KEY` line. Added comment explaining user-provided key model.

- [x] **Step QF-5: Backend — instantiate AIService once per batch**
  - Moved `AIService()` instantiation before the article loop in `article_processor.py`. Single client reused for all articles in a batch.

- [x] **Step QF-6: Backend — parse `published_at` datetime explicitly**
  - Added `_parse_datetime()` helper using `datetime.fromisoformat()` with `Z` → `+00:00` conversion and try/except fallback to `None`.

- [x] **Step QF-7: Remove dead code**
  - Removed `NewsFetcher.fetch_everything()` from `news_fetcher.py`. Removed `truncateText()` from `utils.ts`.

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
| 15 | QF-1 | Fix broken font configuration | DONE |
| 16 | QF-2 | Settings dialog → ShadCN Dialog (focus trap) | DONE |
| 17 | QF-3 | Error handling UI (surface API errors) | DONE |
| 18 | QF-4 | Fix .env.template (remove NEWS_API_KEY) | DONE |
| 19 | QF-5 | AIService instantiation (once per batch) | DONE |
| 20 | QF-6 | Parse published_at datetime explicitly | DONE |
| 21 | QF-7 | Remove dead code | DONE |
| 22 | Step 15 | End-to-end integration testing | TODO |
| 23 | Step 16 | Developer experience | TODO |
| 24 | Step 17 | Legacy cleanup | TODO |

**Next**: Step 15 — end-to-end integration testing.
