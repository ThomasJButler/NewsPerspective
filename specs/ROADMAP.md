# NewsPerspective Roadmap

## Purpose

This file captures future-facing product direction, content guardrails, and design intent that should survive implementation churn. It is not a promise that every item ships immediately. The immediate next-loop sequence still comes from `IMPLEMENTATION_PLAN.md`.

Anything here becomes part of the active v3 runtime contract only after it is promoted into `specs/OVERVIEW.md`, `specs/BACKEND.md`, or `specs/FRONTEND.md`.

## Product Intent

NewsPerspective is not a portfolio demo. The goal is to help readers cut through sensationalism, misinformation, doom-heavy framing, and emotionally manipulative headline culture.

The app should make it easier to:

1. Read calmer, factual versions of stories.
2. Find genuinely constructive or positive stories.
3. Avoid categories and topics that are emotionally harmful or unwanted.
4. Understand how the same story is framed across outlets and countries.

## Content Guardrails (Shipped)

Content guardrails are enforced at query time in both the normal feed and Good News mode. Stories matching guardrail keywords are hidden from browse results but remain in the database for audit purposes.

Excluded topics:

- War stories (warfare, airstrike, bombing, armed conflict, etc.)
- Suicide stories (suicide, suicidal, self-harm)
- Depression stories (depression, depressed, mental health crisis)
- Death-related stories (death toll, killed, murder, homicide, fatally, found dead)
- Grief-related stories (grief, grieving, mourning, funeral, vigil)

Rationale:

- These topics are difficult to rewrite safely into a calmer tone.
- They can be emotionally triggering.
- They increase the risk of harmful misinterpretation or accidental false framing.

## Good News Rules

Good News should be opinionated, not just a generic positive sentiment toggle.

Current v3 behavior now excludes `sports`, `entertainment`, and `politics` in the shipped backend/frontend flow.

Shipped rules:

- `sports` should not count toward Good News.
- `entertainment` should not count toward Good News.
- `politics` should not count toward Good News.

The current `politics` exclusion uses app-level topic detection in the backend Good News path because NewsAPI does not provide a dedicated `politics` category in the existing fetch loop. Those exclusions should stay enforced consistently in the backend classification/filtering path and reflected clearly in the frontend UX.

## Feed And Filtering

### Country-aware reading (Shipped)

Users can browse articles by country using the CountryFilter component. Dual US+GB fetch is implemented in the backend. Country badges appear on article cards. Country-specific framing differences are part of the product value, not just an implementation detail.

### Category filtering (Shipped)

Users can filter by broad topics such as `general`, `sports`, `entertainment`, `technology`, and other NewsAPI categories via the CategoryFilter component. The backend exposes `GET /api/categories` for dynamic category counts.

### Future filtering work

- Users should be able to hide certain topics entirely to reduce emotional triggering.
- Users should be able to choose up to 10 preferred topics in Settings, and refresh should fetch only those selected topics when possible.
- Articles should be analysed for topic, not just passed through with the source category. Over time the app should distinguish between source-provided category labels and app-derived topic classification.

## Feed UX Direction

### Processing visibility

- The feed should only show articles once they are fully analysed.
- Newly fetched stories should appear progressively as they finish processing.
- The UI should make the background work visible with polished animations, loading states, and clear status messaging.
- Users should understand what is happening behind the scenes during refresh without reading technical logs.

### Visual refinements (Shipped)

Article cards use full-width 16:9 banner images with error fallback. Header content is aligned with the article feed via `max-w-3xl`. Remaining polish: loading transition animations.

### Headline rewrite visibility (Shipped)

`getVisibleHeadline()` ensures rewritten headlines are displayed when available, with fallback to the original. `_validate_result` normalisation ensures blank rewrites are cleaned up at processing time.

## Article Comparison (Shipped)

Evolved from the original "Fact Checker Mode" concept. A dedicated `/comparison` page showing how the same story is framed differently across sources and countries.

Shipped scope:

- Backend: `GET /api/comparison` (fuzzy title matching to group related articles), `POST /api/comparison/analyse` (one AI call per group)
- Frontend: side-by-side card layout with AI analysis panel
- One story group at a time for the initial version
- Optimise for thoughtful comparison rather than bulk processing

## Accessibility (Partially Shipped)

Accessibility is a product requirement, not a polish-only task.

Shipped:

- `aria-label` on CountryFilter, SourceFilter, and CategoryFilter select triggers
- `<nav>` landmark wrapping the filter bar
- `aria-live="polite"` on StatsBar for article count announcements
- `aria-busy` on refresh button during processing
- ShadCN Dialog focus trapping (Radix UI built-in)
- Search input, refresh, and settings buttons have explicit `aria-label`s

Remaining:

- `aria-describedby` on good-news toggle
- `prefers-reduced-motion` in CSS
- `focus-visible` utilities

## About Modal (Shipped)

The About modal (`about-modal.tsx`) is accessible via a header button. It explains the app, shows how it works, and includes links to the GitHub repository and Buy Me a Coffee. Footer shows v3.0.0, attribution, and AGPLv3 license.

## Developer Note To Users

Planned message for the About experience or similar UI:

- the app is free to use today
- it will remain ad-free
- clean UX and design are part of the mission
- the product exists to help people cut through manipulative framing and make news consumption feel calmer and more human

## Data And Source Constraints

- NewsPerspective is a self-hosted personal project. The free NewsAPI tier restricts requests to localhost and delays articles by ~24 hours.
- The 24-hour window works well for the app's purpose: it gives the AI time to analyse and contextualise stories instead of racing to publish raw headlines.
- If the project grows, alternative news sources (Guardian API, RSS, NewsData.io) could be explored via the pluggable news source architecture.

## Build Queue

The immediate execution sequence is tracked in `IMPLEMENTATION_PLAN.md`. This roadmap captures product direction only; it does not own the build queue.
