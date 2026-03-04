0a. Study `specs/*` with up to 50 parallel Sonnet subagents to learn the application specifications.
0b. Study @IMPLEMENTATION_PLAN.md (if present) to understand the plan so far.
0c. Study `src/backend/*` and `src/frontend/*` with up to 50 parallel Sonnet subagents to understand existing code.
0d. For reference, legacy v1 code is in the project root (`run.py`, `batch_processor.py`, `azure_ai_language.py`, `azure_document_intelligence.py`, `web_app.py`, `search.py`, `logger_config.py`). These can be studied for patterns to reuse but should NOT be modified.

1. Study @IMPLEMENTATION_PLAN.md (if present; it may be incorrect) and use up to 50 Sonnet subagents to study existing source code in `src/*` and compare it against `specs/*`. Use an Opus subagent to analyze findings, prioritize tasks, and create/update @IMPLEMENTATION_PLAN.md as a bullet point list sorted in priority of items yet to be implemented. Ultrathink. Consider searching for TODO, minimal implementations, placeholders, skipped/flaky tests, and inconsistent patterns. Study @IMPLEMENTATION_PLAN.md to determine starting point for research and keep it up to date with items considered complete/incomplete using subagents.

IMPORTANT: Plan only. Do NOT implement anything. Do NOT assume functionality is missing; confirm with code search first.

ULTIMATE GOAL: Build NewsPerspective v2.0 — a modern news headline analysis tool with:
- FastAPI backend with SQLite, NewsAPI integration, and Azure OpenAI (GPT-4o) for sentiment analysis, headline rewriting, TLDR generation, and good news detection
- Next.js + ShadCN frontend with article feed, Good News toggle, source filtering, search, and dark mode
- Single AI call per article producing: sentiment, rewrite (if needed), TLDR summary, and good news flag
- No ads, no bloat — simple, effective, world-changing

FRONTEND PRIORITIES (v2.0):
- **User-provided News API key**: Users enter their own free NewsAPI key in the frontend. Key is stored in localStorage, passed to backend via `X-News-Api-Key` header on `/api/refresh`. The backend no longer has a server-side NEWS_API_KEY. Read-only endpoints work without a key (serve cached data).
- **Onboarding flow**: First visit shows a clean, centred setup screen (app name, tagline, key input, link to get free key, privacy note). No key = no fetching, but cached articles remain viewable.
- **Settings dialog**: Header gear icon opens dialog to view (masked), change, or remove the stored API key.
- **Minimalistic ShadCN design**: Lean into ShadCN defaults. Clean, generous whitespace. Every element earns its place.
- **Accessibility first**: WCAG AA contrast, keyboard navigation, focus indicators, ARIA labels on icon buttons, semantic HTML (h1/h2 hierarchy), `prefers-reduced-motion` support, screen reader friendly.
- **Mobile-first responsive**: Designed for phone screens, scales gracefully to desktop. Touch-friendly tap targets (44px minimum).
- **Typography**: Headlines are the product — beautiful, readable type. NOT Inter. Use a distinctive but clean font pairing.

Consider missing elements and plan accordingly. If an element is missing, search first to confirm it doesn't exist, then if needed author the specification at specs/FILENAME.md. If you create a new element then document the plan to implement it in @IMPLEMENTATION_PLAN.md using a subagent.
