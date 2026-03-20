# NewsPerspective Roadmap

## Purpose

This file captures future-facing product direction, content guardrails, and design intent that should survive implementation churn. It is not a promise that every item ships immediately. The immediate next-loop sequence still comes from `IMPLEMENTATION_PLAN.md`.

Anything here becomes part of the active v2 runtime contract only after it is promoted into `specs/OVERVIEW.md`, `specs/BACKEND.md`, or `specs/FRONTEND.md`.

## Product Intent

NewsPerspective is not a portfolio demo. The goal is to help readers cut through sensationalism, misinformation, doom-heavy framing, and emotionally manipulative headline culture.

The app should make it easier to:

1. Read calmer, factual versions of stories.
2. Find genuinely constructive or positive stories.
3. Avoid categories and topics that are emotionally harmful or unwanted.
4. Understand how the same story is framed across outlets and countries.

## Planned Content Guardrails

These are product-direction guardrails for a future implementation phase. They are not enforced by the current v2 runtime yet, and the active specs should not imply that they already ship. Once implemented, they should apply to both the normal feed and Good News mode unless a later active spec explicitly narrows them:

- Exclude war stories for now.
- Exclude suicide stories.
- Exclude depression stories.
- Exclude death-related stories.
- Exclude grief-related stories.

Rationale:

- These topics are difficult to rewrite safely into a calmer tone.
- They can be emotionally triggering.
- They increase the risk of harmful misinterpretation or accidental false framing.

## Good News Rules

Good News should be opinionated, not just a generic positive sentiment toggle.

Current v2 behavior now excludes `sports`, `entertainment`, and `politics` in the shipped backend/frontend flow.

Shipped rules:

- `sports` should not count toward Good News.
- `entertainment` should not count toward Good News.
- `politics` should not count toward Good News.

The current `politics` exclusion uses app-level topic detection in the backend Good News path because NewsAPI does not provide a dedicated `politics` category in the existing fetch loop. Those exclusions should stay enforced consistently in the backend classification/filtering path and reflected clearly in the frontend UX.

## Feed And Filtering Roadmap

### Country-aware reading

- Users should be able to browse articles by country.
- Country should matter in both the normal feed and future comparison workflows.
- Country-specific framing differences are part of the product value, not just an implementation detail.

### Topic-aware reading

- Users should be able to filter by broad topics such as `general`, `sports`, `entertainment`, `politics`, `technology`, and other supported categories.
- Users should be able to hide certain topics entirely to reduce emotional triggering.
- Users should be able to choose up to 10 preferred topics in Settings, and refresh should fetch only those selected topics when possible.

### Topic analysis

- Articles should be analysed for topic, not just passed through with the source category.
- Over time the app should distinguish between source-provided category labels and app-derived topic classification.

## Feed UX Direction

### Processing visibility

- The feed should only show articles once they are fully analysed.
- Newly fetched stories should appear progressively as they finish processing.
- The UI should make the background work visible with polished animations, loading states, and clear status messaging.
- Users should understand what is happening behind the scenes during refresh without reading technical logs.

### Visual refinements

- Add a small thumbnail to article cards in the main feed.
- Align the header content with the article stack so the layout feels tidy and streamlined.
- Improve the overall polish of the feed and loading transitions.

### Headline rewrite visibility

- When an article has a rewritten headline, the feed should clearly show that rewritten version in the list experience instead of silently falling back to the original.
- Investigate and fix the current-feed behavior where rewritten headlines are not always appearing as expected.

## Fact Checker Mode

### Core idea

Add a separate mode called `Fact Checker`.

This mode should:

- take one article story at a time, not the whole feed
- compare how that story is published across different sites
- compare the framing across countries when country filtering is available
- help surface whether ownership, incentives, or editorial framing appear to push doom-heavy or misleading interpretations

### Scope guardrails

- Only one story at a time for the initial version.
- Optimize for thoughtful comparison rather than bulk processing.
- Treat this as a deliberate research mode, not a background feed refresh.

## Accessibility

Accessibility is a product requirement, not a polish-only task.

Planned expectations:

- strong keyboard support
- meaningful focus states
- accessible modals, toggles, and filter controls
- clear loading and status messaging for screen readers
- motion that respects reduced-motion preferences

## About Modal

Add an About toggle/button near the theme toggle.

The modal should explain:

- what the app is
- why it was built
- how to use it

It should also include:

- a GitHub button
- a Buy Me a Coffee button

Links can be filled manually later.

## Developer Note To Users

Planned message for the About experience or similar UI:

- the app is free to use today
- it will remain ad-free
- clean UX and design are part of the mission
- the product exists to help people cut through manipulative framing and make news consumption feel calmer and more human

## Monetization Direction

Free mode should remain ad-free. No ads in free mode, ever.

If the app becomes widely used, future monetization may be one of:

- a one-time app purchase
- a small monthly subscription

Reason:

- a business-tier NewsAPI setup could materially improve the experience
- that future model would allow latest-news coverage and more advanced filtering/personalization without requiring user-supplied NewsAPI keys
- that future business-tier NewsAPI cost may be on the order of hundreds of dollars per month, so any paid plan should offset a real infrastructure cost rather than introduce ads
- the goal would be to offset real platform/API cost, not turn the product into an ad-driven experience

If a paid tier ever exists, it should remain aligned with the core mission:

- better filtering
- better personalization
- better access to current stories
- still no ads

## Data And Source Constraints

- The current free NewsAPI flow is limited to recent coverage rather than true live same-day exhaustiveness.
- The current 24-hour-ish window can still be used productively because it gives the app time to analyse and contextualize stories instead of racing to publish raw headlines.

## Near-Term Loop Order

Do not let roadmap work scramble the immediate execution order.

Recently completed loops already landed the refresh-status surface, the Good News exclusions for `sports`, `entertainment`, and `politics`, the timeout-resume frontend spec alignment, and the visible-headline runtime fix.

The current intended sequence is now:

1. Current build-mode loop:
   Clean up this roadmap section so it reflects the actual remaining priorities instead of pointing at completed slices.
2. Next build loop:
   Close the remaining backend refresh-router review cleanup tracked in `IMPLEMENTATION_PLAN.md` by making the validation exception chaining explicit in `src/backend/routers/sources.py`.
3. After that cleanup:
   Re-evaluate roadmap-only product-direction items against `IMPLEMENTATION_PLAN.md` before promoting any new work into the active specs.
