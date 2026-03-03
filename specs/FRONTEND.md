# Frontend Specification

## Technology

- **Framework**: Next.js 15 (App Router)
- **UI Library**: ShadCN/ui
- **Styling**: Tailwind CSS
- **No ads, no tracking, no bloat**

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
│   │   └── tldr-section.tsx     # TLDR summary component
│   ├── lib/
│   │   ├── api.ts               # API client for backend
│   │   └── utils.ts             # Utility functions
│   └── types/
│       └── article.ts           # TypeScript types
```

## Pages

### Home (/)
The main news feed. Clean, minimal, scannable.

Layout:
```
┌─────────────────────────────────────────────┐
│  NewsPerspective              [Search]       │
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
4. **Mobile-first** — most news is consumed on phones
5. **No visual noise** — no ads, no pop-ups, no cookie banners, no newsletter prompts
6. **Dark mode support** — via ShadCN's built-in theme system

## API Integration

The frontend calls the FastAPI backend. In development:
- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- Next.js `rewrites` in `next.config.js` to proxy `/api/*` to backend

In production, both can be served from the same domain or via reverse proxy.
