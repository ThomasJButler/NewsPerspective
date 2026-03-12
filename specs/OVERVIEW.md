# NewsPerspective v2.0 - Overview

## Mission

NewsPerspective helps readers compare sensational framing against a calmer, factual presentation of the same story. The product focuses on three outcomes:

1. Rewrite loaded headlines only when the original framing is misleading, sensational, or needlessly emotional.
2. Generate short TLDR summaries from the article description so the story can be understood quickly.
3. Surface genuinely positive stories with a dedicated good-news filter.

For future-facing product direction, content guardrails, and roadmap items that are not yet part of the active implementation slice, see `specs/ROADMAP.md`.

## Core Principles

- Simple: cached browse should work without a saved NewsAPI key.
- Accurate: rewrites must preserve facts and never invent context.
- Transparent: the original headline remains visible beside any rewritten version.
- Practical: one refresh request should fetch, analyse, and persist articles with minimal operator setup.

## Current Architecture

```text
┌──────────────────────────────────────────────────────────┐
│ Frontend (Next.js 16 + React 19 + ShadCN UI)            │
│ - Cached article browsing                               │
│ - Search, source, and good-news filters                 │
│ - Inline onboarding and refresh UI                      │
│ - Polling for refresh status                            │
└──────────────────────────┬───────────────────────────────┘
                           │ /api/*
┌──────────────────────────▼───────────────────────────────┐
│ Backend (FastAPI)                                        │
│ - GET /api/articles and GET /api/articles/{id}           │
│ - GET /api/sources and GET /api/stats                    │
│ - POST /api/refresh and GET /api/refresh/status          │
│ - Background refresh processing                          │
│ - In-memory per-process refresh tracking                 │
└───────────────┬───────────────────────┬──────────────────┘
                │                       │
        ┌───────▼────────┐      ┌───────▼─────────────────┐
        │ NewsAPI        │      │ OpenAI chat completions │
        │ /v2/top-headlines      │ Single analysis call    │
        │ country=us             │ per article             │
        └────────┬───────┘      └────────┬─────────────────┘
                 │                        │
                 └──────────────┬─────────┘
                                ▼
                         SQLite via SQLAlchemy
```

## Runtime Rules

- The backend does not own a server-side `NEWS_API_KEY`.
- Refresh requests must include the user's key in the `X-News-Api-Key` header.
- Read-only endpoints continue to serve cached processed articles without a NewsAPI key.
- Each article is analysed in a single OpenAI call that returns sentiment, rewrite decision/output, TLDR, and the good-news flag.
- The shipped good-news filter now excludes `sports` and `entertainment` stories in addition to the backend `is_good_news` signal.
- The roadmap-only `politics` exclusion and broader topic/content guardrails remain future work until they are promoted into the active specs and implemented.
- SQLite is the active persistence layer for v2.

## What Changed From v1

- Azure-era runtime assumptions were removed from the active app.
- Direct OpenAI API usage replaced Azure OpenAI wiring in the v2 backend.
- SQLite replaced Azure Search and other hosted indexing dependencies.
- The frontend moved to Next.js plus ShadCN UI instead of the older root-level runtime approach.
- The old root-level v1 runtime files were removed from the checked-out repo on 2026-03-10; use git history or the archived legacy docs when older implementation details need to be inspected.

## External Dependencies

- NewsAPI provides the source headlines used during refresh.
- OpenAI provides the per-article analysis and rewrite output.
- SQLite stores the cached article corpus used by the read-only browse experience.
