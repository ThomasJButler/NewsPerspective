# Completed Implementation Archive

Created: 2026-03-10

This archive captures work that was fully completed and removed from the active `IMPLEMENTATION_PLAN.md` after reviewing current plan state and git history through commit `3810d00`.

## Source basis
- Current `IMPLEMENTATION_PLAN.md` before cleanup.
- Git history reviewed from `ee4d5d5` through `3810d00`.
- Commit history for `IMPLEMENTATION_PLAN.md` and recent landed v2 work.

## Architecture and foundation
- 2026-03-04 `ee4d5d5` completed Phase 1 backend foundation:
  - active FastAPI app assembly in `src/backend/main.py`
  - API routers under `src/backend/routers/`
  - shared response schemas in `src/backend/schemas.py`
  - article-processing pipeline in `src/backend/services/article_processor.py`
  - request-scoped NewsAPI key handling instead of a server-owned `NEWS_API_KEY`
  - live article, article-detail, source, stats, and refresh endpoints
- 2026-03-10 `6940e61` and `216350c` removed unused legacy root files from the checked-out tree and tightened the v2 working boundary.
- 2026-03-10 `e83a153` added a supported Docker-based frontend local/test path.

## Backend changes
- 2026-03-05 `eb72797` landed backend quality fixes:
  - reuse `AIService` across a batch instead of per article
  - parse `published_at` with explicit datetime handling
  - remove dead fetch and utility code
- 2026-03-09 `a030bfa` and `c865189` updated backend setup and environment documentation and relocated backend requirements into the v2 structure.
- 2026-03-10 `dafcdcc` added structured backend refresh errors.
- 2026-03-10 `cc8a629` switched the default NewsAPI fetch contract to US headlines.
- 2026-03-10 `0b8a268` completed the normalized-source backend slice.
- 2026-03-10 `77304eb` added backend seed helpers and test package files.
- 2026-03-10 `0943942`, `80b1a40`, `dbc4bd8`, `eccffda`, and `3810d00` closed the refresh-correctness slice:
  - NewsAPI fetch failures now raise `NewsFetchError` instead of ending as a false-success empty refresh.
  - Background refresh processing now marks refresh state as failed when `NewsFetchError` escapes.
  - Request and HTTP error strings redact the NewsAPI key before messages reach logs or `/api/refresh/status`.
  - Duplicate-refresh frontend responses no longer create accepted-key feedback or misleading success copy.

## Frontend changes
- 2026-03-04 `6867b2b` completed Step 9:
  - Next.js frontend scaffold
  - ShadCN setup
  - v2 frontend app structure under `src/frontend/`
- 2026-03-04 `ed50fa8` completed Step 10:
  - TypeScript app types
  - API client utilities
  - shared hooks and frontend helpers
- 2026-03-04 `e424bef` completed Step 11 core UI components.
- 2026-03-04 `bb23a2c` completed Steps 12 through 14:
  - home page feed and filter flow
  - article detail route
  - theme support and dark mode
- 2026-03-05 `eb72797` completed frontend quality fixes:
  - system font fallback cleanup
  - ShadCN dialog-based settings modal
  - toast-driven API error feedback
  - article-detail and page-level polish tied to those fixes
- 2026-03-10 `ea1bb26` improved frontend refresh error handling.
- 2026-03-10 `3bf9a15` polished frontend local state and tooling.
- 2026-03-10 `738bcac` fixed Next.js config alignment.
- 2026-03-10 `49274c6` added frontend DX guardrails for learning.
- 2026-03-10 `e83a153` added frontend Docker assets, updated the frontend runtime guide, and adjusted Playwright config for the supported local path.

## Testing and validation
- 2026-03-10 `0c65e40` added the manual integration evidence helper flow.
- 2026-03-10 `efa45d2` added seeded Playwright coverage for the cached-browse path.
- 2026-03-10 `dbc4bd8` added repo-owned backend regression coverage for refresh processing.
- 2026-03-10 planning validation recorded the following passing commands:
  - `python -m unittest src.backend.tests.test_api_smoke -v`
  - `python -m unittest src.backend.tests.test_refresh_processing -v`
  - `cd src/frontend && npm run lint`
  - `cd src/frontend && npm run typecheck`
- 2026-03-10 planning review also captured the current command caveat:
  - running `src.backend.tests.test_refresh_processing` and `src.backend.tests.test_api_smoke` in one Python interpreter is unreliable because both modules set `DATABASE_URL` at import time for different temp databases

## Documentation and developer workflow
- 2026-03-09 and 2026-03-10 doc/tooling work landed across `a030bfa`, `c865189`, `1d72779`, `4d03075`, and `e83a153`:
  - backend setup documentation refresh
  - `.env.template` cleanup for the v2 contract
  - frontend README improvements
  - loop and local workflow guidance
  - Docker-local instructions for the frontend stack

## Closed review and planning work on 2026-03-10
- Re-read repo rules, current plan, README context, specs, recent git history, and the live backend/frontend source.
- Searched for repo-local issue tracker files and written code-review notes. None were found.
- Re-checked current worktree state before updating the plan.
- Re-ran the smallest current validation set before closing Step 17.5.
- Closed Step 17.5 as complete and moved the next active focus to Step 17.6 frontend regressions, then trusted-machine evidence, then refresh-path browser coverage.
