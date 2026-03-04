# Frontend Specification

## Technology

- **Framework**: Next.js 15 (App Router)
- **UI Library**: ShadCN/ui
- **Styling**: Tailwind CSS
- **No ads, no tracking, no bloat**

## Design Philosophy

**Minimalistic, accessible, effortless.** The frontend is a reading tool — it should disappear and let the content breathe. Every element earns its place. No decoration for decoration's sake.

- **ShadCN defaults** — lean into the component library's clean aesthetic, don't fight it
- **Accessibility first** — proper ARIA labels, keyboard navigation, focus rings, screen reader support, sufficient contrast ratios (WCAG AA minimum)
- **Mobile-first responsive** — designed for phones, scales up beautifully to desktop
- **User-provided News API key** — no server-side news key needed; each user enters their own free NewsAPI key to fetch headlines

## User-Provided API Key Flow

Users bring their own [NewsAPI key](https://newsapi.org/register) (free tier: 100 requests/day).

1. **First visit**: Clean onboarding screen — brief explanation of what the app does, input for News API key, link to get a free key
2. **Key stored in `localStorage`** — never sent to any third party, only passed to our backend as a request header (`X-News-Api-Key`)
3. **Key validation**: Backend validates the key with a lightweight NewsAPI call before proceeding
4. **Key management**: Small settings icon in header to view/change/remove the stored key
5. **No key = no news fetching** — but previously fetched articles remain viewable from the backend database

The backend's Azure OpenAI key remains server-side (deployment operator's cost). Only the news source key is user-provided.

## Project Structure

```
src/
├── frontend/
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   ├── components.json          # ShadCN config
│   ├── app/
│   │   ├── layout.tsx           # Root layout with metadata
│   │   ├── page.tsx             # Home — news feed
│   │   ├── globals.css          # Tailwind base + custom
│   │   └── article/
│   │       └── [id]/
│   │           └── page.tsx     # Article detail view
│   ├── components/
│   │   ├── ui/                  # ShadCN components
│   │   ├── article-card.tsx     # News article card
│   │   ├── article-feed.tsx     # Paginated article list
│   │   ├── good-news-toggle.tsx # The "Good News" switch
│   │   ├── source-filter.tsx    # Filter by news source
│   │   ├── search-bar.tsx       # Search articles
│   │   ├── header.tsx           # Site header
│   │   ├── stats-bar.tsx        # Processing stats display
│   │   ├── tldr-section.tsx     # TLDR summary component
│   │   ├── api-key-setup.tsx    # API key onboarding + input
│   │   └── settings-dialog.tsx  # Key management dialog
│   ├── hooks/
│   │   ├── use-api-key.ts       # localStorage-backed API key hook
│   │   └── use-debounce.ts      # Debounce hook for search
│   ├── lib/
│   │   ├── api.ts               # API client (attaches X-News-Api-Key header)
│   │   └── utils.ts             # Utility functions
│   └── types/
│       └── article.ts           # TypeScript types
```

## Pages

### First Visit (no API key stored)
Clean onboarding. No clutter. Gets the user started in 30 seconds.

```
┌─────────────────────────────────────────────┐
│                                              │
│            NewsPerspective                   │
│       See the news. Not the spin.            │
│                                              │
│  News headlines are designed to grab your    │
│  attention, not inform you. We fix that.     │
│                                              │
│  ┌─────────────────────────────────────────┐ │
│  │  Enter your News API key               │ │
│  │  [________________________] [Get Started]│ │
│  │                                         │ │
│  │  Free key → newsapi.org/register        │ │
│  └─────────────────────────────────────────┘ │
│                                              │
│  Your key stays in your browser.             │
│  We never store or share it.                 │
│                                              │
└─────────────────────────────────────────────┘
```

### Home (/) — with API key
The main news feed. Clean, minimal, scannable.

```
┌─────────────────────────────────────────────┐
│  NewsPerspective        [Search] [⚙️] [🌙]  │
│  See the news. Not the spin.                 │
├─────────────────────────────────────────────┤
│                                              │
│  [Good News Toggle]  [Source Filter ▾]       │
│                                              │
├─────────────────────────────────────────────┤
│                                              │
│  ┌─ Article Card ──────────────────────────┐ │
│  │ BBC News • 2 hours ago                  │ │
│  │                                         │ │
│  │ Rewritten Headline (large, clear)       │ │
│  │                                         │ │
│  │ TLDR: 2-3 sentence summary of the      │ │
│  │ actual story, accurate and balanced.    │ │
│  │                                         │ │
│  │ Original: "SENSATIONAL HEADLINE!!!"     │ │
│  │ (smaller, muted, expandable)            │ │
│  │                                         │ │
│  │ [Read Full Article →]                   │ │
│  └─────────────────────────────────────────┘ │
│                                              │
│  ┌─ Article Card ──────────────────────────┐ │
│  │ ...                                     │ │
│  └─────────────────────────────────────────┘ │
│                                              │
│  [Load More]                                 │
│                                              │
└─────────────────────────────────────────────┘
```

### Article Detail (/article/[id])
Full article view with more context.

## Components

### ArticleCard
The core UI element. Shows:
1. **Source + timestamp** (top, small, muted)
2. **Rewritten headline** (primary, large) — or original if no rewrite needed
3. **TLDR summary** (2-3 sentences, readable font size)
4. **Original headline** (collapsible, shown as "Original: ..." in muted text)
5. **Read Full Article** link (opens original source in new tab)

If the article was NOT rewritten (already neutral/positive), just show the headline normally without the "Original:" comparison.

### GoodNewsToggle
A prominent ShadCN Switch component.
- OFF (default): Show all news
- ON: Show only articles flagged as `is_good_news`
- Should feel satisfying to toggle — this is the "power" moment

### SourceFilter
ShadCN Select dropdown. Filter by source (BBC, Guardian, etc.)

### SearchBar
ShadCN Input. Searches across headlines. Debounced, 300ms.

### StatsBar (optional, subtle)
Small bar showing "147 articles processed today • 89 headlines improved"

## Design Principles

1. **Clean white/light background** — easy on the eyes
2. **Excellent typography** — headlines are the product, they must be beautifully typeset
3. **Generous whitespace** — not cramped, not overwhelming
4. **Mobile-first** — most news is consumed on phones; touch-friendly tap targets (min 44px)
5. **No visual noise** — no ads, no pop-ups, no cookie banners, no newsletter prompts
6. **Dark mode support** — via ShadCN's built-in theme system (next-themes)
7. **Accessible** — WCAG AA contrast, semantic HTML, keyboard navigable, screen reader friendly
8. **Simple** — if a feature doesn't directly serve the user reading news, it doesn't exist

## Accessibility Requirements

- All interactive elements keyboard-accessible with visible focus indicators
- ARIA labels on icon-only buttons (settings, theme toggle, refresh)
- Semantic heading hierarchy (h1 for page title, h2 for article headlines)
- `prefers-reduced-motion` respected — disable animations for users who request it
- Sufficient color contrast in both light and dark themes
- Form inputs have associated labels (API key input, search bar)
- External links marked with `rel="noopener noreferrer"` and visually indicated

## API Integration

The frontend calls the FastAPI backend. In development:
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- Next.js `rewrites` in `next.config.js` to proxy `/api/*` to backend

**API key header**: All requests that trigger news fetching (refresh) include `X-News-Api-Key` header with the user's stored key. Read-only endpoints (articles, sources, stats) work without a key — they serve cached data from the backend database.

In production, both can be served from the same domain or via reverse proxy.
