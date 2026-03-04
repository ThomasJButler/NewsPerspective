# Implementation Plan -- NewsPerspective v2.0

> **Status**: Phase 2 (Frontend) in progress. Steps 1-10 done. Step 11 (Core UI components) next.

---

## Spec Gaps to Resolve During Implementation

These gaps exist in the current specs. They do not block starting work, but must be resolved by the time the relevant step is reached. The plan notes inline where each gap becomes relevant.

1. **GET /api/articles/:id response shape** -- BACKEND.md says "single article with full detail" but does not define the JSON shape. Resolve: return the full Article schema (same fields as in the list response, unwrapped from the array).
2. **GET /api/sources response shape** -- not defined. Resolve: `{ "sources": [{ "source_name": str, "source_id": str, "article_count": int }] }`.
3. **GET /api/stats response shape** -- not defined. Resolve: `{ "total_articles": int, "rewritten_count": int, "good_news_count": int, "sources_count": int, "latest_fetch": datetime|null }`.
4. **POST /api/refresh response shape** -- not defined. Resolve: `{ "status": "processing", "message": str }` returned immediately; processing is async.
5. **Error response shape** -- not defined anywhere. Resolve: use FastAPI default `{ "detail": str }` with appropriate HTTP status codes.
6. **Article Detail page (/article/[id]) layout** -- FRONTEND.md lists the route but provides no wireframe or component breakdown. Resolve: full-width single article view showing all fields (rewritten title, original title, TLDR, source, author, published date, sentiment badge, image if available, link to original).
7. **header.tsx component** -- listed in the project structure but not described in FRONTEND.md components section. Resolve: site name "NewsPerspective", tagline "See the news. Not the spin.", search bar (or link to it), theme toggle, and optional refresh button.
8. **TldrSection component details** -- listed but not described. Resolve: a styled blockquote/card showing the TLDR text with a "TLDR" label, visually distinct from the headline.
9. **Image handling when image_url is null** -- not specified. Resolve: hide the image area entirely (no placeholder) when null.
10. **NewsAPI free tier rate limiting** -- 100 req/day limit not addressed. Resolve: track request count in the news_fetcher, log warnings at 80+ requests, refuse to fetch at 100. Consider caching/dedup to minimize calls.
11. **No authentication on API** -- acceptable for v2.0 MVP (local/demo use). Document as a future concern.
12. **User-provided News API key** -- users enter their own NewsAPI key in the frontend (stored in localStorage). The backend accepts this key via `X-News-Api-Key` header on `POST /api/refresh`. This eliminates the need for a server-side `NEWS_API_KEY` and avoids shared rate limits. Read-only endpoints (articles, sources, stats) work without a key — they serve cached data from the database.

---

## Phase 1: Backend Foundation

All backend work lives in `src/backend/`. Each step must be fully functional before moving on -- no stubs or placeholders.

- [x] **Step 1: Project scaffolding + configuration**
  - Create directory structure: `src/backend/`, `src/backend/routers/`, `src/backend/services/`, `src/backend/utils/`
  - Create `__init__.py` in each package directory
  - `src/backend/config.py` -- pydantic-settings `Settings` class loading from `.env`: `AZURE_OPENAI_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_DEPLOYMENT` (default `gpt-4o`), `DATABASE_URL` (default `sqlite:///./newsperspective.db`). Note: `NEWS_API_KEY` is no longer a server-side setting — users provide their own via the frontend.
  - `src/backend/database.py` -- SQLAlchemy engine, `SessionLocal` factory, declarative `Base`, `get_db()` dependency
  - `src/backend/models.py` -- `Article` ORM model with all 18 columns per BACKEND.md schema (id UUID PK, url UNIQUE, processing_status, sentiment fields, etc.)
  - `src/backend/utils/logger.py` -- simplified rotating logger reusing patterns from root `logger_config.py`
  - Verify `.env.template` already has v2 vars (it does -- confirmed)
  - Verify `.gitignore` already covers node_modules/, .next/, *.db, __pycache__/ (it does -- confirmed)
  - **Dependencies**: none (first step)

- [x] **Step 2: AI service**
  - `src/backend/services/__init__.py`
  - `src/backend/services/ai_service.py` -- `AIService` class wrapping Azure OpenAI chat completions
  - Single method `analyse_article(title: str, source: str, description: str) -> dict` that returns: `sentiment`, `sentiment_score`, `needs_rewrite`, `rewritten_title`, `rewrite_reason`, `tldr`, `is_good_news`
  - System prompt and user prompt template exactly as specified in `specs/AI_PROMPTS.md`
  - JSON response parsing with fallback on malformed response (return neutral defaults, mark as failed)
  - Uses `openai` Python SDK with Azure configuration (chat completions, not legacy completions)
  - **Dependencies**: Step 1 (config for API keys)

- [x] **Step 3: News fetcher**
  - `src/backend/services/news_fetcher.py` -- `NewsFetcher` class
  - Constructor accepts `api_key: str` parameter (user-provided, not from server config) **(resolves spec gap #12)**
  - `fetch_top_headlines(country="gb", category=None)` -- UK top headlines via NewsAPI `/v2/top-headlines`
  - `fetch_everything(query="UK", sort_by="publishedAt")` -- broader search via `/v2/everything`
  - Returns normalized list of article dicts with consistent field names matching the DB schema
  - Filter out removed/empty articles (NewsAPI returns `[Removed]` placeholders)
  - Rate limit handling: catch HTTP 429, log warning, implement basic retry with backoff
  - **(Spec gap #10)**: Log warnings approaching daily request limit
  - **Dependencies**: Step 1 (config)

- [x] **Step 4: Article processor**
  - `src/backend/services/article_processor.py` -- `ArticleProcessor` class (or module-level functions)
  - `process_new_articles(db: Session)` -- full orchestration: fetch articles -> dedup by URL against DB -> AI analysis for each new article -> save to DB
  - Dedup: query DB for existing URLs, skip matches
  - Set `processing_status` = `pending` on insert, update to `processed` on success, `failed` on error
  - Catch per-article exceptions so one failure does not abort the batch
  - Must be compatible with `FastAPI BackgroundTasks` (accepts a db session or creates its own)
  - **Dependencies**: Steps 1-3

- [x] **Step 5: Pydantic schemas**
  - `src/backend/schemas.py` -- response models:
    - `ArticleResponse` -- all article fields serialized for JSON (id as str, datetimes as ISO strings)
    - `ArticleListResponse` -- `{ articles: list[ArticleResponse], total: int, page: int, per_page: int, has_more: bool }`
    - `SourceResponse` -- `{ sources: list[SourceItem] }` where `SourceItem` = `{ source_name: str, source_id: str, article_count: int }` **(resolves spec gap #2)**
    - `StatsResponse` -- `{ total_articles: int, rewritten_count: int, good_news_count: int, sources_count: int, latest_fetch: datetime|None }` **(resolves spec gap #3)**
    - `RefreshResponse` -- `{ status: str, message: str }` **(resolves spec gap #4)**
  - **Dependencies**: Step 1 (models for field reference)

- [x] **Step 6: API routers**
  - `src/backend/routers/__init__.py`
  - `src/backend/routers/articles.py`:
    - `GET /api/articles` -- paginated, filterable by `good_news_only`, `source`, `category`, `search` (title substring match). Returns `ArticleListResponse`.
    - `GET /api/articles/{id}` -- returns single `ArticleResponse` or 404. **(Resolves spec gap #1)**
  - `src/backend/routers/sources.py`:
    - `GET /api/sources` -- distinct sources with article counts. Returns `SourceResponse`.
    - `GET /api/stats` -- aggregate counts. Returns `StatsResponse`.
    - `POST /api/refresh` -- requires `X-News-Api-Key` header (user's NewsAPI key). Returns 401 if missing/invalid. Validates key with a lightweight NewsAPI call, then triggers `process_new_articles` via `BackgroundTasks` passing the user's key. Returns `RefreshResponse` immediately. **(Resolves spec gaps #4 and #12)**
  - **Dependencies**: Steps 4-5

- [x] **Step 7: FastAPI app assembly**
  - `src/backend/main.py` -- create FastAPI app, add CORS middleware (allow `http://localhost:3000`), include both routers, lifespan event to call `Base.metadata.create_all()` on startup
  - **Dependencies**: Step 6

- [x] **Step 8: Backend verification**
  - Start server: `cd src/backend && uvicorn main:app --reload --port 8000`
  - Verify `GET /api/articles` returns `{ "articles": [], "total": 0, ... }`
  - Verify `GET /api/sources` returns `{ "sources": [] }`
  - Verify `GET /api/stats` returns zeroed stats
  - Verify `POST /api/refresh` returns 200 and triggers background processing
  - Wait briefly, then verify `GET /api/articles` returns processed articles
  - Verify `GET /api/articles/{id}` returns a single article
  - Fix any issues found before proceeding to frontend
  - **Dependencies**: Step 7

---

## Phase 2: Frontend

All frontend work lives in `src/frontend/`. The backend must be functional (Phase 1 complete) before integration testing, but frontend scaffolding and components can be built referencing the known API shapes.

- [x] **Step 9: Next.js + ShadCN scaffolding**
  - `npx create-next-app@latest src/frontend` -- TypeScript, Tailwind CSS, App Router, no src/ subfolder within frontend
  - `cd src/frontend && npx shadcn@latest init`
  - Add ShadCN components: Button, Card, Switch, Select, Input, Badge, Skeleton, Separator
  - Configure `next.config.js` (or `next.config.ts`) with rewrites: `/api/:path*` -> `http://localhost:8000/api/:path*`
  - **Dependencies**: None (can run in parallel with backend, but verify separately)

- [x] **Step 10: TypeScript types + API client + utilities + hooks**
  - `src/frontend/types/article.ts` -- `Article`, `ArticleListResponse`, `Source`, `SourcesResponse`, `Stats`, `StatsResponse` interfaces matching backend schemas
  - `src/frontend/hooks/use-api-key.ts` -- custom hook backed by `localStorage`: `{ apiKey, setApiKey, clearApiKey, hasApiKey }`. Uses `useState` + `useEffect` to sync with localStorage. Key stored under `"newsperspective-api-key"`.
  - `src/frontend/hooks/use-debounce.ts` -- generic debounce hook for search input (300ms default)
  - `src/frontend/lib/api.ts` -- `fetchArticles(params)`, `fetchArticle(id)`, `fetchSources()`, `fetchStats()`, `refreshArticles(apiKey)` functions using `fetch()` against `/api/...` (proxied). The `refreshArticles` function includes `X-News-Api-Key` header. Read-only functions do not need the key.
  - `src/frontend/lib/utils.ts` -- `formatDate()` (relative time like "2 hours ago"), `truncateText()`, ShadCN `cn()` utility (may already exist from init)
  - **Dependencies**: Step 9

- [ ] **Step 11: Core UI components**
  - `src/frontend/components/api-key-setup.tsx` -- Onboarding screen shown when no API key is stored. Clean, centred layout: app name, tagline, brief explanation, ShadCN Input for key, "Get Started" button, link to newsapi.org/register, privacy note ("Your key stays in your browser"). Uses `useApiKey` hook.
  - `src/frontend/components/settings-dialog.tsx` -- ShadCN Dialog triggered from header settings icon. Shows current key (masked), option to change or remove it. Accessible: proper focus trap, ESC to close, ARIA labels.
  - `src/frontend/components/header.tsx` -- site name, tagline, search bar, settings icon button (gear), theme toggle, refresh button. All icon buttons have `aria-label`. Responsive: stacks on mobile. **(resolves spec gap #7)**
  - `src/frontend/components/article-card.tsx` -- source+time, rewritten headline (large, `<h2>`), TLDR section, original headline (muted, collapsible via `<details>`/`<summary>` for native accessibility), "Read Full Article" external link with `rel="noopener noreferrer"`. If not rewritten, show headline normally without original comparison. Handle null `image_url` by omitting image area. **(resolves spec gap #9)**
  - `src/frontend/components/tldr-section.tsx` -- styled blockquote/card with "TLDR" label **(resolves spec gap #8)**
  - `src/frontend/components/good-news-toggle.tsx` -- ShadCN Switch with associated `<label>` "Good News Only"
  - `src/frontend/components/source-filter.tsx` -- ShadCN Select dropdown populated from `/api/sources`, with "All Sources" default option
  - `src/frontend/components/search-bar.tsx` -- ShadCN Input with `aria-label="Search articles"`, uses `useDebounce` hook (300ms)
  - `src/frontend/components/stats-bar.tsx` -- subtle bar: "X articles processed · Y headlines improved"
  - `src/frontend/components/article-feed.tsx` -- renders list of ArticleCards, "Load More" button for pagination, ShadCN Skeleton loading states, empty state message when no articles found
  - **Dependencies**: Step 10

- [ ] **Step 12: Home page**
  - `src/frontend/app/layout.tsx` -- root layout with metadata (title, description, viewport for mobile), theme provider wrapper. Use a clean, readable system font stack or a distinctive serif/sans pairing — NOT Inter (see design principles).
  - `src/frontend/app/page.tsx` -- checks `useApiKey().hasApiKey`: if false, renders `ApiKeySetup`; if true, renders the news feed layout. Composes: Header, filters bar (GoodNewsToggle + SourceFilter), StatsBar, ArticleFeed. Manages filter state via URL search params (shareable). Auto-triggers refresh on first load if no articles exist.
  - `src/frontend/app/globals.css` -- Tailwind base styles, ShadCN CSS variables, `@media (prefers-reduced-motion: reduce)` rules
  - **Dependencies**: Step 11

- [ ] **Step 13: Article detail page**
  - `src/frontend/app/article/[id]/page.tsx` -- full article detail view **(resolves spec gap #6)**:
    - Fetch single article via `GET /api/articles/{id}`
    - Display: rewritten title (large), original title (if rewritten, shown with "Original:" label), TLDR section, source name, author, published date, sentiment badge (positive/neutral/negative with color), article image (if available), "Read Full Article" link to original URL
    - Back navigation to home
    - Loading skeleton while fetching
    - 404 handling if article not found
  - **Dependencies**: Steps 10-11
  - **Note**: This page was in FRONTEND.md's project structure but missing from the original plan

- [ ] **Step 14: Dark mode**
  - `src/frontend/components/theme-provider.tsx` -- `next-themes` ThemeProvider wrapping the app
  - `src/frontend/components/theme-toggle.tsx` -- sun/moon icon toggle button, placed in Header
  - Update `layout.tsx` to wrap children with ThemeProvider
  - Verify all components respect dark mode (ShadCN handles most of this automatically)
  - **Dependencies**: Step 12

---

## Phase 3: Integration and Polish

- [ ] **Step 15: End-to-end integration testing**
  - Start both backend (`uvicorn`) and frontend (`npm run dev`) simultaneously
  - `POST /api/refresh` to trigger article processing
  - Verify articles render in the frontend with rewritten headlines and TLDR summaries
  - Test Good News toggle filters to only `is_good_news` articles
  - Test source filter dropdown populates and filters correctly
  - Test search bar filters by headline text with debounce
  - Test article detail page navigation and rendering
  - Test dark mode toggle
  - Test "Load More" pagination
  - Test empty states (no articles, no search results)
  - Fix any issues discovered
  - **Dependencies**: Phases 1 and 2 complete

- [ ] **Step 16: Developer experience**
  - Root `Makefile` with targets:
    - `dev` -- start both backend and frontend concurrently
    - `backend` -- start backend only
    - `frontend` -- start frontend only
    - `refresh` -- `curl -X POST http://localhost:8000/api/refresh`
    - `install` -- install both Python and Node dependencies
  - Update `CLAUDE.md` with v2.0 commands (replace v1 commands)
  - Update `AGENTS.md` with new build/run/validate instructions (keep it brief and operational)
  - **Dependencies**: Step 15

- [ ] **Step 17: Legacy cleanup**
  - Move legacy v1 files to `legacy/` directory: `run.py`, `batch_processor.py`, `azure_ai_language.py`, `azure_document_intelligence.py`, `web_app.py`, `search.py`, `logger_config.py`, `loop.sh`
  - Move `rewrites.png` to `legacy/`
  - Update `README.md` for v2.0 (new architecture, new setup instructions, new screenshots)
  - Final `.gitignore` review
  - **Dependencies**: Step 16

---

## Implementation Order Summary

| Priority | Step | Description | Blocked By |
|----------|------|-------------|------------|
| 1 | Step 1 | Project scaffolding + config | -- |
| 2 | Step 2 | AI service | Step 1 |
| 3 | Step 3 | News fetcher | Step 1 |
| 4 | Step 4 | Article processor | Steps 1-3 |
| 5 | Step 5 | Pydantic schemas | Step 1 |
| 6 | Step 6 | API routers | Steps 4-5 |
| 7 | Step 7 | FastAPI app assembly | Step 6 |
| 8 | Step 8 | Backend verification | Step 7 |
| 9 | Step 9 | Next.js + ShadCN scaffolding | -- |
| 10 | Step 10 | Types + API client + utilities + hooks | Step 9 |
| 11 | Step 11 | Core UI components | Step 10 |
| 12 | Step 12 | Home page | Step 11 |
| 13 | Step 13 | Article detail page | Steps 10-11 |
| 14 | Step 14 | Dark mode | Step 12 |
| 15 | Step 15 | End-to-end integration testing | Steps 8, 14 |
| 16 | Step 16 | Developer experience | Step 15 |
| 17 | Step 17 | Legacy cleanup | Step 16 |

**Parallelism note**: Steps 2 and 3 can be built in parallel (both depend only on Step 1). Step 5 can be built in parallel with Steps 2-4. Step 9 (frontend scaffolding) can begin at any time, even alongside Phase 1. Steps 12 and 13 can be built in parallel.
