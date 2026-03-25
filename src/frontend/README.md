# Frontend

Next.js frontend for NewsPerspective v3.0. The app proxies `/api/*` requests to the FastAPI backend, supports cached browsing without a saved NewsAPI key, and includes seeded Playwright coverage for both the cached-browse and refresh-path flows.

## Local run

From `src/frontend`:

```bash
npm install
npm run dev
```

The frontend expects the backend on `http://localhost:8000` by default. Override that at startup with `BACKEND_ORIGIN` if needed.

## Playwright

Run the local Playwright suite with the repo-managed harness:

```bash
npm run test:e2e
```

This path seeds a clean e2e SQLite database, then starts backend and frontend servers on fixed ports:

- backend: `127.0.0.1:8000`
- frontend: `127.0.0.1:3000`

Use it only when Playwright owns those ports. If either port is already in use, the run will fail before test execution.

If you already have the app running locally and want Playwright to reuse that stack instead of starting its own servers, run:

```bash
npm run test:e2e:reuse
```

That script expects your existing frontend at `http://127.0.0.1:3000` and the backend behind its normal `/api/*` proxy path.

Trusted-machine refresh evidence is currently recorded in `../../logs/phase3_manual_integration_report.md`.

If you need to refresh that evidence on a trusted local machine, run only the refresh-path spec against that existing local stack:

```bash
npm run test:e2e:reuse -- tests/e2e/refresh-path.spec.ts
```

Pair that with the backend helper from the repo root:

```bash
source src/backend/.venv/bin/activate
export NEWS_API_KEY=your_real_key
python -m src.backend.scripts.capture_manual_integration_evidence \
  --output /tmp/phase3-manual-integration.md
```

The Playwright spec still uses mocked API responses. Its role in this trusted-machine evidence flow is to prove the documented browser entrypoint works outside the sandbox while the helper and manual browser notes capture the real-key backend behavior.
The helper reads `NEWS_API_KEY` from the caller environment so the real key stays out of argv during local runs.

Successful runs emit named screenshots under `output/playwright/test-results/`, including:

- `cached-browse-home.png`
- `cached-browse-filtered-results.png`
- `cached-browse-article-detail.png`

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
