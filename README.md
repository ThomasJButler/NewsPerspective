# NewsPerspective

**See the news. Not the spin.**

NewsPerspective uses AI to rewrite sensationalised headlines, generate TLDR summaries, and analyse sentiment across US and UK news sources. Stay informed without the fear-mongering, exaggeration, and ad clutter.

- Sensationalised headlines are rewritten to be calm and factual
- Every article gets a short TLDR summary
- Sentiment analysis shows the tone of each story
- Good News filter surfaces genuinely positive stories
- Content guardrails hide war, death, and other distressing topics
- Country and category filters let you focus on what matters
- No ads, no tracking, no account required

## Quick Start

You need three things: Python 3.11+, Node 22+, and a free [NewsAPI key](https://newsapi.org/register). An [OpenAI API key](https://platform.openai.com/api-keys) powers the AI analysis.

### 1. Clone and set up the backend

```bash
git clone https://github.com/ThomasJButler/NewsPerspective.git
cd NewsPerspective

python3 -m venv src/backend/.venv
source src/backend/.venv/bin/activate
pip install -r src/backend/requirements.txt
```

### 2. Configure environment

Copy `.env.template` to `.env` at the repo root and add your OpenAI key:

```env
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini
DATABASE_URL=sqlite:///./newsperspective.db
```

Your NewsAPI key is never stored on the server. You enter it in the browser and it stays in your browser's local storage.

### 3. Start the backend

```bash
source src/backend/.venv/bin/activate
uvicorn src.backend.main:app --reload --port 8000
```

### 4. Start the frontend

In a second terminal:

```bash
cd src/frontend
npm install
npm run dev
```

### 5. Open and refresh

Open [http://localhost:3000](http://localhost:3000). Cached articles are browseable immediately. To fetch fresh headlines, enter your NewsAPI key in the inline setup card and hit the refresh button.

## How It Works

```text
Browser (Next.js 16 + React 19 + ShadCN UI)
    │
    │  /api/* proxy
    ▼
Backend (FastAPI + SQLite)
    │
    ├── NewsAPI /v2/top-headlines (US + UK, 7 categories)
    │
    └── OpenAI chat completions (one call per article)
            → sentiment, rewrite decision, TLDR, good-news flag
```

1. You hit refresh. The frontend sends your NewsAPI key in the `X-News-Api-Key` header.
2. The backend fetches headlines from NewsAPI across both US and UK sources in 7 categories (general, sports, technology, science, health, business, entertainment).
3. Each new article gets a single OpenAI analysis call that decides whether the headline needs rewriting, generates a TLDR, scores sentiment, and flags good news.
4. Processed articles are stored in SQLite and served to the frontend. Read-only browsing works without any API key.

## Personalise the AI

The AI prompt that analyses each article lives in `src/backend/services/ai_service.py`. You can customise it to match your reading preferences.

Here is a Claude/ChatGPT prompt you can use to generate a personalised version:

```
I'm setting up NewsPerspective (https://github.com/ThomasJButler/NewsPerspective).
The AI system prompt is in src/backend/services/ai_service.py.

Help me customise the analysis prompt for my preferences:

- Topics I care about: [e.g. technology, climate, local UK news]
- Topics I want to avoid: [e.g. celebrity gossip, US politics]
- Tone I prefer: [e.g. formal and concise / casual and explanatory]
- Good news criteria: [e.g. only scientific breakthroughs / any positive community story]
- TLDR length: [e.g. 1 sentence / 2-3 sentences / detailed paragraph]

Generate a replacement system prompt that keeps the JSON response
format but adjusts the analysis rules and rewrite style to match.
```

## NewsAPI Free Tier

The free NewsAPI plan gives you 100 requests per day with articles delayed by ~24 hours. NewsPerspective fetches 7 categories across 2 countries, so each refresh uses ~14 requests. That means roughly 7 refreshes per day on the free plan.

This works well for the app's purpose: it gives the AI time to analyse and contextualise stories rather than racing to publish raw headlines.

If the project grows, a future premium hosted version may use a business-tier NewsAPI plan for real-time coverage. The self-hosted version will always remain free and ad-free.

## Docker

A Docker Compose workflow is included for quick local testing:

```bash
# Start the app stack (seeds demo data automatically)
docker compose -f src/frontend/compose.yaml up --build app

# Run Playwright e2e tests against the stack
docker compose -f src/frontend/compose.yaml run --rm playwright

# Stop
docker compose -f src/frontend/compose.yaml down
```

## Development

### Validation

Backend tests (98 tests across 6 modules):

```bash
source src/backend/.venv/bin/activate
python -m unittest src.backend.tests.test_api_smoke -v
python -m unittest src.backend.tests.test_refresh_processing -v
python -m unittest src.backend.tests.test_manual_integration_evidence -v
python -m unittest src.backend.tests.test_config -v
python -m unittest src.backend.tests.test_comparison -v
python -m unittest src.backend.tests.test_custom_guardrails -v
```

Frontend checks:

```bash
cd src/frontend
npm run lint
npm run typecheck
npm run test:e2e
```

If ports 3000/8000 are already in use from a running local stack, use `npm run test:e2e:reuse` instead.

### Project Structure

```text
src/
├── backend/
│   ├── main.py              # FastAPI app entrypoint
│   ├── models.py            # SQLAlchemy article model
│   ├── routers/             # API route handlers
│   ├── services/            # AI, news fetching, article processing
│   ├── utils/               # Good news rules, content guardrails
│   └── tests/               # Backend test suite
└── frontend/
    ├── app/                  # Next.js App Router pages
    ├── components/           # React components (ShadCN UI)
    ├── hooks/                # Custom React hooks
    ├── lib/                  # API client, utilities
    ├── types/                # TypeScript type definitions
    └── tests/e2e/            # Playwright browser tests
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, React 19, ShadCN UI, Tailwind CSS 4 |
| Backend | FastAPI, SQLAlchemy, OpenAI Python SDK |
| Database | SQLite |
| News source | NewsAPI (free tier compatible) |
| AI | OpenAI chat completions (default: gpt-4o-mini) |
| Testing | Python unittest, Playwright |

## Contributing

Contributions are welcome. Please open an issue first to discuss what you would like to change.

By submitting a pull request, you agree that your contributions may be subject to a Contributor License Agreement (CLA). This allows the project to maintain flexibility for future licensing while keeping the open-source version available under AGPLv3.

## License

[AGPLv3](LICENSE) — free to use, modify, and distribute. If you run a modified version as a network service, you must share your changes under the same license.

Built by [Tom Butler](https://github.com/ThomasJButler).
