# NewsPerspective v2.0 — Overview

## Mission

News headlines are designed to grab attention, not inform. Sensationalism, negativity bias, and misleading framing create a "chinese whispers" effect — even when the original story is factual, the headline distorts perception, and that distortion ripples outward with real consequences.

NewsPerspective gives power back to the reader by:

1. **Rewriting headlines** to be factual and unbiased — stripping sensationalism while preserving truth
2. **Generating accurate TLDR summaries** so readers get the real story in seconds
3. **Surfacing good news** that exists but gets buried by the attention economy

## Core Principles

- **Simple** — No bloat, no ads, no tracking. A clean tool that does one thing well.
- **Accurate** — Never fabricate, always preserve facts. The rewrite must be MORE truthful, not less.
- **Transparent** — Always show the original headline alongside the rewrite so users can compare.
- **Fast** — Users should see today's news immediately, not wait for batch processing.

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  Frontend (Next.js + ShadCN)     │
│  - News feed with rewritten headlines            │
│  - TLDR summaries per article                    │
│  - "Good News" toggle                            │
│  - Source/category filtering                     │
│  - Original vs rewritten comparison              │
└──────────────────────┬──────────────────────────┘
                       │ REST API
┌──────────────────────▼──────────────────────────┐
│                  Backend (FastAPI)                │
│  - /api/articles — paginated article feed        │
│  - /api/articles/:id — single article detail     │
│  - /api/refresh — trigger article processing     │
│  - /api/sources — available news sources         │
│  - /api/stats — processing statistics            │
└──────────┬───────────┬──────────────────────────┘
           │           │
    ┌──────▼──┐  ┌─────▼──────┐
    │ NewsAPI │  │ Azure      │
    │         │  │ OpenAI     │
    └─────────┘  │ (GPT-4o)  │
                 └────────────┘
           │
    ┌──────▼──────┐
    │  SQLite DB  │
    │  (articles) │
    └─────────────┘
```

## Key Simplifications from v1

- **Drop Azure AI Language** — GPT-4o handles sentiment analysis better inline
- **Drop Azure Document Intelligence** — Not needed; NewsAPI provides article descriptions, and GPT-4o can work with those
- **Drop Azure Search** — SQLite is simpler, free, and sufficient for this use case
- **Replace Streamlit** with a proper Next.js + ShadCN frontend
- **Replace completions endpoint** with chat completions (GPT-4o or equivalent)
- **Single processing pipeline** instead of duplicated logic in run.py and batch_processor.py

## Data Source

NewsAPI (https://newsapi.org) — free tier provides 100 requests/day, which is plenty for pulling latest headlines. Only requires `NEWS_API_KEY`.
