# Backend Specification

## Technology

- **Framework**: FastAPI (Python)
- **Database**: SQLite via SQLAlchemy (simple, zero-config, portable)
- **AI**: OpenAI chat completions API
- **News Source**: NewsAPI (https://newsapi.org)
- **Task runner**: Background task processing via FastAPI BackgroundTasks

## Project Structure

```
src/
├── backend/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, CORS, lifespan
│   ├── config.py             # Environment config with pydantic-settings
│   ├── database.py           # SQLAlchemy engine, session, Base
│   ├── models.py             # SQLAlchemy ORM models
│   ├── schemas.py            # Pydantic request/response schemas
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── articles.py       # /api/articles endpoints
│   │   └── sources.py        # /api/sources endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   ├── news_fetcher.py   # NewsAPI integration
│   │   ├── article_processor.py  # Orchestrates analysis + rewrite + TLDR
│   │   └── ai_service.py     # OpenAI wrapper (sentiment, rewrite, TLDR)
│   └── utils/
│       ├── __init__.py
│       └── logger.py         # Logging config
```

## Database Schema

### articles table

| Column | Type | Description |
|--------|------|-------------|
| id | TEXT (UUID) | Primary key |
| original_title | TEXT | Original headline from NewsAPI |
| rewritten_title | TEXT | AI-rewritten unbiased headline |
| tldr | TEXT | 2-3 sentence accurate summary |
| original_description | TEXT | Article description from NewsAPI |
| source_name | TEXT | News source (BBC, Guardian, etc.) |
| source_id | TEXT | NewsAPI source identifier |
| author | TEXT | Article author |
| url | TEXT (UNIQUE) | Original article URL (dedup key) |
| image_url | TEXT | Article image URL |
| published_at | DATETIME | Original publication time |
| fetched_at | DATETIME | When we fetched it |
| was_rewritten | BOOLEAN | Whether headline was rewritten |
| original_sentiment | TEXT | positive/neutral/negative |
| sentiment_score | REAL | -1.0 to 1.0 sentiment score |
| is_good_news | BOOLEAN | Flagged as positive/good news |
| category | TEXT | News category (general, sports, tech, etc.) |
| processing_status | TEXT | pending/processed/failed |

## API Endpoints

### GET /api/articles
Paginated article feed.

Query params:
- `page` (int, default 1)
- `per_page` (int, default 20, max 50)
- `good_news_only` (bool, default false)
- `source` (string, optional)
- `category` (string, optional)
- `search` (string, optional — full text search on titles)

Response:
```json
{
  "articles": [...],
  "total": 150,
  "page": 1,
  "per_page": 20,
  "has_more": true
}
```

### GET /api/articles/:id
Single article with full detail.

### POST /api/refresh
Trigger fetching and processing new articles. Returns immediately, processing happens in background.

**Requires `X-News-Api-Key` header** — the user's own NewsAPI key. Returns 401 if missing. The backend validates the key by making a lightweight NewsAPI call before starting the background job. If the key is invalid, returns 401 with an error message.

### GET /api/sources
List available news sources with article counts.

### GET /api/stats
Processing statistics (total articles, rewrites, good news count, etc.)

## Services

### news_fetcher.py
- Fetch latest articles from NewsAPI `/v2/top-headlines` and `/v2/everything`
- UK-focused but configurable
- Deduplication by URL
- Categories: general, sports, technology, science, health, business, entertainment

### ai_service.py
Single OpenAI service that handles all AI tasks via chat completions:

1. **Analyse & Rewrite** — Single prompt that:
   - Assesses sentiment (positive/neutral/negative with score)
   - Determines if rewrite needed (sensational, misleading, or unnecessarily negative)
   - Rewrites headline to be factual and unbiased (if needed)
   - Generates accurate TLDR summary (2-3 sentences)
   - Flags if this is "good news" (genuinely positive story)

This is done in ONE API call to be efficient. The prompt returns structured JSON.

2. **System prompt** emphasises:
   - Never fabricate facts
   - Preserve all factual content
   - Remove sensationalism, clickbait, and unnecessary negativity
   - TLDR must be accurate to the article content
   - "Good news" means genuinely positive stories, not just neutral ones

### article_processor.py
Orchestrates the pipeline:
1. Takes raw articles from news_fetcher
2. Skips articles already in database (dedup by URL)
3. Calls ai_service for each new article
4. Saves processed articles to database

## Environment Variables

```env
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4o-mini
DATABASE_URL=sqlite:///./newsperspective.db
```

Note: `NEWS_API_KEY` is no longer a server-side environment variable. Users provide their own NewsAPI key via the frontend, which passes it to the backend as an `X-News-Api-Key` request header on `/api/refresh`.

If `OPENAI_API_KEY` is not configured, fetched articles are still stored, but AI-derived fields fall back to neutral defaults.

## Error Handling

- NewsAPI failures: log and retry with backoff
- OpenAI failures: log and fall back to neutral analysis defaults without crashing ingestion
- All services return clean error responses, never crash the server
