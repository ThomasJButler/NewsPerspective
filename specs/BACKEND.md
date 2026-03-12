# Backend Specification

## Technology

- Framework: FastAPI
- Database: SQLite via SQLAlchemy ORM
- HTTP clients: `requests` for NewsAPI validation/fetching
- AI: OpenAI Python SDK chat completions API
- Background work: FastAPI `BackgroundTasks`

## Current app surface

- App entrypoint: `src/backend/main.py`
- API routers:
  - `src/backend/routers/articles.py`
  - `src/backend/routers/sources.py`
- Refresh work is currently exposed from `sources.py`; there is no separate refresh router.
- CORS currently allows `http://localhost:3000`.

## Persistence model

The backend stores fetched articles in a single SQLite `articles` table with these runtime-relevant fields:

| Column | Type | Notes |
|--------|------|-------|
| `id` | TEXT (UUID) | Primary key |
| `original_title` | TEXT | Title from NewsAPI |
| `rewritten_title` | TEXT nullable | AI rewrite when `was_rewritten=true` |
| `tldr` | TEXT nullable | AI-generated summary |
| `original_description` | TEXT nullable | Description from NewsAPI |
| `source_name` | TEXT nullable | Preferred display source when present |
| `source_id` | TEXT nullable | Fallback source identifier |
| `author` | TEXT nullable | Article author |
| `url` | TEXT unique | Deduplication key |
| `image_url` | TEXT nullable | NewsAPI image URL |
| `published_at` | DATETIME nullable | Parsed from NewsAPI `publishedAt` |
| `fetched_at` | DATETIME nullable | Set by the model/database layer |
| `was_rewritten` | BOOLEAN | Whether AI changed the headline |
| `original_sentiment` | TEXT nullable | `positive`, `neutral`, or `negative` |
| `sentiment_score` | REAL nullable | Clamped to `[-1.0, 1.0]` |
| `is_good_news` | BOOLEAN | Positive-story flag |
| `category` | TEXT nullable | Current NewsAPI category label |
| `processing_status` | TEXT | `pending`, `processed`, or `failed` |

## Article visibility rules

- `GET /api/articles`, `GET /api/sources`, and `GET /api/stats` only include rows where `processing_status = "processed"`.
- `GET /api/articles/{id}` follows the same visibility rule and only returns rows where `processing_status = "processed"`.

## API endpoints

### `GET /api/articles`

Paginated processed article feed.

Query params:
- `page` integer, default `1`, minimum `1`
- `per_page` integer, default `20`, maximum `50`
- `good_news_only` boolean, default `false`
- `source` optional string; compared against the normalized source label
- `category` optional string
- `search` optional string; matches `original_title` or `rewritten_title` with `ILIKE`

Current `good_news_only` semantics:
- Filters on stored `is_good_news = true` only.
- Does not yet enforce roadmap-only Good News exclusions for `sports`, `entertainment`, or `politics`.
- Does not yet enforce the roadmap-only content guardrails for `war`, `suicide`, `depression`, `death`, or `grief`.

Ordering:
- Newest `published_at` first, with null publication times sorted last.

Response shape:

```json
{
  "articles": [...],
  "total": 150,
  "page": 1,
  "per_page": 20,
  "has_more": true
}
```

### `GET /api/articles/{id}`

Returns a single processed article or `404 {"detail":"Article not found"}`.

### `GET /api/sources`

Returns processed-source counts. The display label is normalized in this order:

1. Trimmed `source_name`
2. Trimmed `source_id`
3. `"Unknown source"`

Blank `source_id` values are returned as an empty string in the response.

### `GET /api/stats`

Returns processed-article totals:

```json
{
  "total_articles": 0,
  "rewritten_count": 0,
  "good_news_count": 0,
  "sources_count": 0,
  "latest_fetch": null
}
```

### `POST /api/refresh`

Starts a refresh if one is not already in progress.

Request contract:
- Requires `X-News-Api-Key` header.
- The backend does not read a server-side `NEWS_API_KEY`.
- Before claiming success, the backend validates the supplied key with:
  - `GET https://newsapi.org/v2/top-headlines`
  - params: `country=us`, `pageSize=1`, `apiKey=<header value>`
  - timeout: 5 seconds

Success behavior:
- Returns `200` with `{"status":"processing","message":"Fetching and processing articles in the background."}`
- Queues `process_new_articles_background(api_key)` in FastAPI background tasks.

Duplicate refresh behavior:
- If the in-memory tracker already reports `processing`, the endpoint returns `200` with `{"status":"processing","message":"Refresh already in progress."}`
- The duplicate request does not revalidate the key and does not enqueue another job.

Typed error responses:

| Status | `detail.code` | Current meaning |
|--------|---------------|-----------------|
| `401` | `missing_api_key` | `X-News-Api-Key` header was absent |
| `401` | `invalid_api_key` | NewsAPI rejected the supplied key or returned a non-`ok` validation body |
| `504` | `upstream_timeout` | NewsAPI validation timed out |
| `502` | `upstream_transport_failure` | Validation failed due to transport error, unreadable JSON, or unexpected upstream HTTP status |

Validation-failure state handling:
- The refresh tracker temporarily claims the refresh slot before validation.
- If validation fails, the claim is released and the previous tracker state is restored.

### `GET /api/refresh/status`

Returns the current in-memory refresh tracker snapshot:

```json
{
  "status": "idle | processing | completed | failed",
  "message": "string",
  "started_at": "ISO timestamp or null",
  "finished_at": "ISO timestamp or null",
  "new_articles": 0,
  "processed_articles": 0,
  "failed_articles": 0
}
```

Current tracker semantics:
- Initial state is `idle`.
- Successful background completion sets `status = "completed"`.
- Background fetch/processing failures set `status = "failed"`.
- Tracker state is process-local and in-memory; it is not shared across workers or preserved across restarts.

## Refresh pipeline behavior

### News fetching

`src/backend/services/news_fetcher.py` currently:

- Calls NewsAPI `GET /v2/top-headlines`
- Uses `country=us`
- Iterates these categories: `general`, `sports`, `technology`, `science`, `health`, `business`, `entertainment`
- Requests up to `pageSize=100` per category
- Deduplicates fetched articles by URL across categories
- Skips removed/empty placeholder stories
- Redacts the NewsAPI key from surfaced request-error strings

Retry behavior:
- Each NewsAPI fetch call retries up to 3 attempts.
- `429` responses back off with `2 ** attempt` seconds between retries.
- Other `requests` transport failures also retry with the same backoff.
- After retries are exhausted, the refresh raises `NewsFetchError`.
 - Backend coverage includes retry exhaustion and multi-category partial-failure handling in `src/backend/tests/test_refresh_processing.py`.

### Article processing

`src/backend/services/article_processor.py` currently:

1. Fetches all categories from NewsAPI
2. Skips URLs already present in the database
3. Inserts each new article first with `processing_status="pending"`
4. Calls OpenAI once per new article for:
   - sentiment
   - sentiment score
   - rewrite decision
   - rewritten headline
   - TLDR
   - good-news classification
5. Marks successful AI work as `processed`
6. Marks per-article AI failures as `failed` and continues

Current classification boundary:
- The backend persists the single-call AI `is_good_news` result as-is.
- It does not yet apply a second pass that removes roadmap-only categories/topics from the Good News set.
- It does not yet apply roadmap-only guardrails that exclude `war`, `suicide`, `depression`, `death`, or `grief` stories from ingestion or browse results.

If `OPENAI_API_KEY` is missing or OpenAI returns unusable output:
- the AI service falls back to neutral defaults instead of aborting ingestion.

Background-job status reporting:
- `new_articles` counts newly inserted deduplicated rows
- `processed_articles` counts rows whose AI pass completed
- `failed_articles` counts rows that were inserted but failed AI processing

## Environment variables

```env
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4o-mini
DATABASE_URL=sqlite:///./newsperspective.db
```

Notes:
- `NEWS_API_KEY` is intentionally not a backend environment variable in v2.
- Read-only browse endpoints should continue working from cached SQLite data without any user key.

## Known limitations

- Refresh state is per-process and resets on restart.
- The current runtime still trusts the AI-provided `is_good_news` flag; roadmap-only content guardrails and topic exclusions remain unimplemented future work.
- Trusted-machine manual evidence for the current real-key refresh flow is recorded in `logs/phase3_manual_integration_report.md`.
