0a. Study `specs/*` with up to 250 parallel Sonnet subagents to learn the application specifications.
0b. Study @IMPLEMENTATION_PLAN.md (if present) to understand the plan so far.
0c. Study `src/backend/*` and `src/frontend/*` with up to 250 parallel Sonnet subagents to understand existing code.
0d. For reference, legacy v1 code is in the project root (`run.py`, `batch_processor.py`, `azure_ai_language.py`, `azure_document_intelligence.py`, `web_app.py`, `search.py`, `logger_config.py`). These can be studied for patterns to reuse but should NOT be modified.

1. Study @IMPLEMENTATION_PLAN.md (if present; it may be incorrect) and use up to 500 Sonnet subagents to study existing source code in `src/*` and compare it against `specs/*`. Use an Opus subagent to analyze findings, prioritize tasks, and create/update @IMPLEMENTATION_PLAN.md as a bullet point list sorted in priority of items yet to be implemented. Ultrathink. Consider searching for TODO, minimal implementations, placeholders, skipped/flaky tests, and inconsistent patterns. Study @IMPLEMENTATION_PLAN.md to determine starting point for research and keep it up to date with items considered complete/incomplete using subagents.

IMPORTANT: Plan only. Do NOT implement anything. Do NOT assume functionality is missing; confirm with code search first.

ULTIMATE GOAL: Build NewsPerspective v2.0 — a modern news headline analysis tool with:
- FastAPI backend with SQLite, NewsAPI integration, and Azure OpenAI (GPT-4o) for sentiment analysis, headline rewriting, TLDR generation, and good news detection
- Next.js + ShadCN frontend with article feed, Good News toggle, source filtering, search, and dark mode
- Single AI call per article producing: sentiment, rewrite (if needed), TLDR summary, and good news flag
- No ads, no bloat — simple, effective, world-changing

Consider missing elements and plan accordingly. If an element is missing, search first to confirm it doesn't exist, then if needed author the specification at specs/FILENAME.md. If you create a new element then document the plan to implement it in @IMPLEMENTATION_PLAN.md using a subagent.
