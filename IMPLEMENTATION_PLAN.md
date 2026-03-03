# Implementation Plan — NewsPerspective v2.0

## Phase 1: Backend Foundation

- [ ] **Step 1: Project structure + config**
  - Create `src/backend/` directory structure per `specs/BACKEND.md`
  - `src/backend/__init__.py`
  - `src/backend/config.py` — pydantic-settings based config loading from `.env` (NEWS_API_KEY, AZURE_OPENAI_KEY, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_DEPLOYMENT, DATABASE_URL)
  - `src/backend/database.py` — SQLAlchemy engine + session factory + Base
  - `src/backend/models.py` — Article ORM model (id, original_title, rewritten_title, tldr, original_description, source_name, source_id, author, url UNIQUE, image_url, published_at, fetched_at, was_rewritten, original_sentiment, sentiment_score, is_good_news, category, processing_status)
  - `src/backend/utils/__init__.py`
  - `src/backend/utils/logger.py` — simplified rotating logger (reuse patterns from root `logger_config.py`)
  - Update `.env.template` with v2 vars (add DATABASE_URL, change AZURE_OPENAI_DEPLOYMENT default to gpt-4o, remove Azure Search/Language/DocIntelligence)
  - Update `.gitignore` (add node_modules/, .next/, *.db, __pycache__/)

- [ ] **Step 2: AI service**
  - `src/backend/services/__init__.py`
  - `src/backend/services/ai_service.py` — Azure OpenAI chat completions wrapper
  - Single `analyse_article(title, source, description)` method
  - System prompt + user prompt per `specs/AI_PROMPTS.md`
  - Returns structured dict: sentiment, sentiment_score, needs_rewrite, rewritten_title, rewrite_reason, tldr, is_good_news
  - JSON response parsing with fallback on parse failure
  - Uses chat completions endpoint (not legacy completions)

- [ ] **Step 3: News fetcher**
  - `src/backend/services/news_fetcher.py`
  - `fetch_top_headlines(country="gb", category=None)` — UK top headlines
  - `fetch_everything(query="UK", sort_by="publishedAt")` — broader search
  - Returns normalised list of article dicts
  - Rate limit handling (429 → wait + retry)
  - Filter out removed/empty articles

- [ ] **Step 4: Article processor**
  - `src/backend/services/article_processor.py`
  - `process_new_articles()` — orchestration: fetch → dedup by URL → AI analysis → save to DB
  - Dedup: skip articles whose URL already exists in database
  - Mark each article processing_status (pending → processed | failed)
  - Compatible with FastAPI BackgroundTasks

- [ ] **Step 5: API schemas + routes**
  - `src/backend/schemas.py` — Pydantic models: ArticleResponse, ArticleListResponse, SourceResponse, StatsResponse, RefreshResponse
  - `src/backend/routers/__init__.py`
  - `src/backend/routers/articles.py` — GET /api/articles (paginated, filterable by good_news_only, source, category, search), GET /api/articles/{id}
  - `src/backend/routers/sources.py` — GET /api/sources (list with counts), GET /api/stats, POST /api/refresh

- [ ] **Step 6: FastAPI app + CORS**
  - `src/backend/main.py` — FastAPI app with CORS (allow localhost:3000), include routers, lifespan event to create DB tables on startup

- [ ] **Step 7: Backend verification**
  - Start server: `cd src/backend && uvicorn main:app --reload --port 8000`
  - Verify GET /api/articles returns empty list
  - Verify POST /api/refresh triggers processing
  - Verify GET /api/articles returns processed articles after refresh

## Phase 2: Frontend

- [ ] **Step 8: Next.js + ShadCN scaffolding**
  - `npx create-next-app@latest src/frontend` (TypeScript, Tailwind, App Router, no src/ subfolder)
  - `cd src/frontend && npx shadcn@latest init`
  - Add ShadCN components: Button, Card, Switch, Select, Input, Badge, Skeleton, Separator
  - Configure `next.config.js` with rewrites: `/api/:path*` → `http://localhost:8000/api/:path*`

- [ ] **Step 9: Types + API client**
  - `src/frontend/types/article.ts` — Article, ArticleListResponse, Source, Stats interfaces
  - `src/frontend/lib/api.ts` — fetchArticles(), fetchSources(), fetchStats(), refreshArticles()
  - `src/frontend/lib/utils.ts` — formatDate(), truncateText()

- [ ] **Step 10: Core components**
  - `src/frontend/components/header.tsx` — "NewsPerspective" + tagline "See the news. Not the spin."
  - `src/frontend/components/article-card.tsx` — rewritten headline (large), TLDR, original headline (muted, collapsible), source + time, Read Full Article link
  - `src/frontend/components/tldr-section.tsx` — styled TLDR block
  - `src/frontend/components/good-news-toggle.tsx` — ShadCN Switch
  - `src/frontend/components/source-filter.tsx` — ShadCN Select
  - `src/frontend/components/search-bar.tsx` — ShadCN Input, debounced 300ms
  - `src/frontend/components/article-feed.tsx` — paginated list with Load More

- [ ] **Step 11: Pages**
  - `src/frontend/app/layout.tsx` — root layout, Inter font, metadata
  - `src/frontend/app/page.tsx` — home page: header + filters bar + article feed
  - `src/frontend/app/globals.css` — Tailwind base

- [ ] **Step 12: Dark mode**
  - `src/frontend/components/theme-provider.tsx` — next-themes provider
  - `src/frontend/components/theme-toggle.tsx` — sun/moon toggle in header

## Phase 3: Integration + Polish

- [ ] **Step 13: End-to-end testing**
  - Start both backend and frontend
  - POST /api/refresh to load articles
  - Verify articles render with rewritten headlines + TLDR
  - Test Good News toggle filters correctly
  - Test source filter and search

- [ ] **Step 14: Developer experience**
  - Root `Makefile` with: `dev`, `backend`, `frontend`, `refresh` targets
  - Update `CLAUDE.md` with v2.0 commands
  - Update `AGENTS.md` with new build/run/validate

- [ ] **Step 15: Cleanup**
  - Move legacy v1 files to `legacy/` directory
  - Update `README.md` for v2.0
  - Update `.gitignore`
