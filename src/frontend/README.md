# Frontend

Next.js frontend for NewsPerspective v2. The app proxies `/api/*` requests to the FastAPI backend, supports cached browsing without a saved NewsAPI key, and includes seeded Playwright coverage for the cached-browse flow.

## Local run

From `src/frontend`:

```bash
npm install
npm run dev
```

The frontend expects the backend on `http://localhost:8000` by default. Override that at startup with `BACKEND_ORIGIN` if needed.

## Playwright

Run the seeded cached-browse spec:

```bash
npx playwright test tests/e2e/cached-browse.spec.ts
```

Successful runs now emit named screenshots under `output/playwright/test-results/`, including:

- `cached-browse-home.png`
- `cached-browse-filtered-results.png`
- `cached-browse-article-detail.png`

If you want Playwright to target an already-running app instead of starting its own frontend and backend, set:

```bash
PLAYWRIGHT_SKIP_WEBSERVER=1 PLAYWRIGHT_BASE_URL=http://127.0.0.1:3000 npx playwright test tests/e2e/cached-browse.spec.ts
```

## Docker

The frontend directory now includes a Docker-based workflow that runs the seeded backend and Next dev server together, plus a separate Playwright runner.

Start the app stack:

```bash
docker compose -f src/frontend/compose.yaml up --build app
```

Open `http://localhost:3000` for the frontend and `http://localhost:8000/api/stats` for the backend health endpoint.

Run the seeded Playwright spec against the containerized app:

```bash
docker compose -f src/frontend/compose.yaml run --rm playwright
```

Stop the stack:

```bash
docker compose -f src/frontend/compose.yaml down
```

If you need to refresh the container-managed `node_modules` volume after dependency changes:

```bash
docker compose -f src/frontend/compose.yaml down -v
```
