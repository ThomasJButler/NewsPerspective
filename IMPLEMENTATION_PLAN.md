# IMPLEMENTATION_PLAN.md

## 1. Current status

Updated 2026-04-08. v3.0 core features complete. Two bugs found blocking UK news and demo readiness:

1. **UK news fetch fragility** — If any single NewsAPI category request fails for GB, the entire refresh dies and even successfully-fetched US articles are lost. Root cause: no per-category or per-country error isolation in `news_fetcher.py` and `article_processor.py`.
2. **Seed data missing country tags** — All 25 seed articles default to `country="us"` despite being from UK sources (BBC, Guardian, Community Wire, FT). Country filter is never exercised with GB data.

## 2. Active phase

Fix UK news, complete QA, ship v3.0.

## 3. Ordered checklist

- [x] Make category fetches resilient in `src/backend/services/news_fetcher.py` — skip failed categories instead of aborting
- [x] Make country fetches independent in `src/backend/services/article_processor.py` — if GB fails, still save US articles
- [x] Update tests in `src/backend/tests/test_refresh_processing.py` to match new resilience contract (116 tests pass, +3 new)
- [x] Add `country` field to seed data in `src/backend/scripts/seed_manual_integration_data.py` — tag UK sources as `"gb"` (20 GB + 5 US)
- [x] Run all backend tests — 116/116 pass, 0 regressions
- [x] Run frontend lint + typecheck — both pass
- [ ] Trusted-machine QA: real-key refresh — verify both US and UK articles appear, test country filter
- [ ] Trusted-machine QA: cached browsing — remove key, verify onboarding card returns and cached articles display
- [ ] Mark v3.0 release-ready

## 4. Notes

- Previous QA items (automated test coverage, frontend static checks, doc alignment) were completed in prior loops.
- The remaining trusted-machine QA steps require a running local stack and a real NewsAPI key entered in the browser.
- App is intentionally self-hosted/localhost-only (NewsAPI free tier constraint). "Production ready" means reliable local operation, not cloud deployment.
