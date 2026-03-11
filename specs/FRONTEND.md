# Frontend Specification

## Scope

The v2 frontend lives in `src/frontend/` and is the user-facing reader for cached and refreshed articles.

- **Framework**: Next.js `16.1.6` with the App Router
- **Runtime**: React `19.2.3`
- **UI stack**: ShadCN/ui primitives, Tailwind CSS 4, `next-themes`
- **Backend integration**: `next.config.ts` rewrites `/api/:path*` to `BACKEND_ORIGIN` (default `http://localhost:8000`)
- **Product rule**: cached articles remain browseable without a saved NewsAPI key; only refresh requests require the user key

The frontend is intentionally minimal: no ads, no analytics, and no account system.

## Current Project Structure

```text
src/frontend/
├── app/
│   ├── article/[id]/page.tsx   # Article detail route
│   ├── globals.css
│   ├── layout.tsx
│   └── page.tsx                # Home route with filters, refresh flow, and inline onboarding
├── components/
│   ├── api-key-setup.tsx
│   ├── article-card.tsx
│   ├── article-feed.tsx
│   ├── good-news-toggle.tsx
│   ├── header.tsx
│   ├── search-bar.tsx
│   ├── settings-dialog.tsx
│   ├── source-filter.tsx
│   ├── stats-bar.tsx
│   ├── theme-provider.tsx
│   ├── theme-toggle.tsx
│   ├── tldr-section.tsx
│   └── ui/
├── hooks/
│   ├── use-api-key.ts
│   ├── use-debounce.ts
│   └── use-toast.ts
├── lib/
│   ├── api.ts
│   └── utils.ts
├── tests/e2e/
│   └── cached-browse.spec.ts
├── compose.yaml
├── next.config.ts
├── playwright.config.mts
└── scripts/docker-start-app.sh
```

## Home Route

`/` is the primary screen for both first-time and returning users.

- The header shows the product title and tagline, a search field, refresh button, theme toggle, and settings button.
- The search box, source filter, and good-news toggle are synchronized with the URL query string.
- Browser back/forward restores those controls from the current URL instead of leaving stale client state behind.
- The article feed is always allowed to render cached backend data, even when no NewsAPI key has been stored.
- The stats bar is only shown when `/api/stats` returns a non-zero article count.

### No Saved Key

The current home-page onboarding is **inline**, not fullscreen.

- When no key is stored in browser storage, the page shows an inline `Fetch fresh headlines` card above the filters and feed.
- That card explains that cached browsing still works and that a NewsAPI key is only needed to fetch new stories.
- Saving a key from the inline card stores it locally and removes the onboarding card.

The `ApiKeySetup` component still supports a `fullscreen` variant, but the running home route currently uses the inline variant.

## API Key Handling

The frontend stores the NewsAPI key in browser `localStorage` under `newsperspective-api-key`.

- The key is managed by `use-api-key.ts` via `useSyncExternalStore`, so multiple tabs react to key changes.
- The settings dialog shows the saved key in masked form, allows add/update/remove, and makes clear that the key stays in the browser until the user requests refresh.
- Saving a key in settings does **not** validate it immediately. Validation happens when the user triggers refresh.
- Removing the key keeps cached articles available and resets the UI back to the inline onboarding guidance.

## Refresh UX

The refresh button in the header is the only frontend action that requires the user-provided NewsAPI key.

### Request flow

1. If no key is currently saved, the frontend does not send a refresh request.
2. It opens settings guidance, scrolls the inline onboarding card into view, and shows a toast explaining that a NewsAPI key is required.
3. If a key exists, the frontend sends `POST /api/refresh` with the `X-News-Api-Key` header.
4. After an accepted response, the frontend polls `GET /api/refresh/status` every second for up to 120 seconds.
5. Once refresh reaches a terminal state, the frontend reloads articles, sources, and stats.

### Error and duplicate handling

- A backend `missing_api_key` error is treated as guidance to re-open key entry UI.
- A backend `invalid_api_key` error opens settings with invalid-key feedback and shows a destructive toast.
- A backend `upstream_timeout` error surfaces a timeout-specific toast, but cached browsing remains available.
- If `POST /api/refresh` returns the duplicate message `Refresh already in progress.`, the frontend treats that as attach-to-existing work and waits on `/api/refresh/status` instead of failing immediately.
- If polling does not reach a terminal state within 120 seconds, the frontend leaves the user on cached content and shows a non-fatal "still running" toast.

### Success feedback

- Successful refreshes show a completion toast that differentiates between new articles and a no-op refresh.
- When the current request validated the saved key, the settings dialog retains a positive "accepted" status message for that key.

## Article Feed and Detail Behavior

### Article cards

- Cards render source and publication time, the visible headline, TLDR text when available, and an external source link.
- Headline rendering uses `getVisibleHeadline(...)`, which falls back to the original title if a rewritten title is blank or missing.
- The original headline is only shown in a disclosure block when the article was rewritten and the visible headline differs from the original.
- Empty states differ based on whether the user has a saved key:
  - saved key: adjust filters or refresh
  - no saved key: browse cache or add a key to fetch fresh headlines

### Article detail route

`/article/[id]` loads the cached article from the backend and differentiates failure modes.

- `404` responses render an `Article not found` state with a link back to the feed.
- Non-`404` failures render an `Unable to load article` state with a `Retry` button.
- Detail pages use the same visible-headline fallback logic as cards.
- The page shows source, author, date, sentiment badge, optional image, TLDR, and the external article link.

## Accessibility and Interaction Baseline

The current implementation includes these concrete accessibility behaviors:

- Search input has an explicit `aria-label`.
- Refresh and settings icon buttons have explicit `aria-label`s.
- The good-news switch is paired with a clickable label.
- External links to NewsAPI and article sources use `rel="noopener noreferrer"`.
- Icon-only controls remain keyboard reachable via the underlying button primitives.

## Local and Docker Flows

### Local development

From `src/frontend/`:

```bash
npm install
npm run dev
```

- The frontend expects the backend at `http://localhost:8000` unless `BACKEND_ORIGIN` is overridden.
- `/api/*` requests are proxied to that backend origin through `next.config.ts`.

### Docker-supported local flow

The frontend repo slice includes a Docker workflow for the seeded local app and Playwright.

```bash
docker compose -f src/frontend/compose.yaml up --build app
docker compose -f src/frontend/compose.yaml run --rm playwright
docker compose -f src/frontend/compose.yaml down
```

- `compose.yaml` runs the backend and Next dev server in one `app` service and exposes ports `3000` and `8000`.
- `scripts/docker-start-app.sh` seeds deterministic backend data before starting the app stack.
- The `playwright` service reuses the app container and runs the seeded cached-browse spec against `http://app:3000`.

## Validation Status and Caveats

Current automated validation for the frontend is limited but useful.

- `npm run lint` and `npm run typecheck` are the routine source-level checks.
- `npx playwright test tests/e2e/cached-browse.spec.ts` is the only deterministic browser spec currently maintained in-repo.
- That Playwright coverage currently proves seeded cached browsing, source/search filtering, browser history re-sync, article-detail retry handling, and visible-headline fallback behavior.

Known caveats:

- Refresh-path browser coverage is still missing for accepted refresh, invalid-key UX, polling UX, and duplicate-refresh messaging.
- Real-key refresh validation is still a trusted-machine/manual task because this Codex environment does not expose `NEWS_API_KEY`.
- `npm run build` may still be environment-sensitive in sandboxed runs because Turbopack can fail while binding worker ports; `npx next build --webpack` was the last known successful fallback in earlier validation.
