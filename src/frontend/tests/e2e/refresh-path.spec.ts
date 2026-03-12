import { expect, test, type Page } from "@playwright/test";

const API_KEY_STORAGE_KEY = "newsperspective-api-key";
const ACCEPTED_REFRESH_MESSAGE =
  "Fetching and processing articles in the background.";
const DUPLICATE_REFRESH_MESSAGE = "Refresh already in progress.";

type TestArticle = {
  id: string;
  original_title: string;
  rewritten_title: string | null;
  tldr: string | null;
  original_description: string | null;
  source_name: string;
  source_id: string;
  author: string;
  url: string;
  image_url: string | null;
  published_at: string;
  fetched_at: string;
  was_rewritten: boolean;
  original_sentiment: string;
  sentiment_score: number;
  is_good_news: boolean;
  category: string;
  processing_status: string;
};

const cachedArticle: TestArticle = {
  id: "cached-story",
  original_title: "Cached headline stays available while refresh runs",
  rewritten_title: null,
  tldr: "Cached articles remain available without blocking on refresh work.",
  original_description: null,
  source_name: "Seeded News",
  source_id: "seeded-news",
  author: "Jordan Lee",
  url: "https://example.com/cached-story",
  image_url: null,
  published_at: "2026-03-10T09:00:00Z",
  fetched_at: "2026-03-10T09:00:00Z",
  was_rewritten: false,
  original_sentiment: "neutral",
  sentiment_score: 0,
  is_good_news: false,
  category: "general",
  processing_status: "processed",
};

const refreshedArticle: TestArticle = {
  id: "refreshed-story",
  original_title: "Fresh article arrives after refresh completes",
  rewritten_title: "Fresh article arrives after refresh completes",
  tldr: "A successful refresh should reload the feed with the latest stories.",
  original_description: null,
  source_name: "Fresh News",
  source_id: "fresh-news",
  author: "Morgan Patel",
  url: "https://example.com/refreshed-story",
  image_url: null,
  published_at: "2026-03-11T10:00:00Z",
  fetched_at: "2026-03-11T10:00:00Z",
  was_rewritten: false,
  original_sentiment: "positive",
  sentiment_score: 0.6,
  is_good_news: true,
  category: "science",
  processing_status: "processed",
};

function buildArticleListResponse(articles: TestArticle[]) {
  return {
    articles,
    total: articles.length,
    page: 1,
    per_page: 20,
    has_more: false,
  };
}

function buildSourcesResponse(articles: TestArticle[]) {
  const sources = Array.from(
    new Map(
      articles.map((article) => [
        article.source_name,
        {
          source_name: article.source_name,
          source_id: article.source_id,
          article_count: 1,
        },
      ])
    ).values()
  );

  return { sources };
}

function buildStatsResponse(articles: TestArticle[]) {
  return {
    total_articles: articles.length,
    rewritten_count: articles.filter((article) => article.was_rewritten).length,
    good_news_count: articles.filter((article) => article.is_good_news).length,
    sources_count: new Set(articles.map((article) => article.source_name)).size,
    latest_fetch: articles[0]?.fetched_at ?? null,
  };
}

async function saveApiKey(page: Page, apiKey: string) {
  await page.addInitScript(
    ({ storageKey, value }) => {
      window.localStorage.setItem(storageKey, value);
    },
    { storageKey: API_KEY_STORAGE_KEY, value: apiKey }
  );
}

async function mockHomeData(page: Page, getArticles: () => TestArticle[]) {
  await page.route("**/api/articles?**", async (route) => {
    const articles = getArticles();
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(buildArticleListResponse(articles)),
    });
  });

  await page.route("**/api/sources", async (route) => {
    const articles = getArticles();
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(buildSourcesResponse(articles)),
    });
  });

  await page.route("**/api/stats", async (route) => {
    const articles = getArticles();
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(buildStatsResponse(articles)),
    });
  });
}

test("completes an accepted refresh and reloads cached data after polling", async ({
  page,
}) => {
  let refreshFinished = false;
  let refreshStatusRequests = 0;

  await saveApiKey(page, "valid-key");
  await mockHomeData(page, () => (refreshFinished ? [refreshedArticle] : [cachedArticle]));

  await page.route("**/api/refresh", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        status: "processing",
        message: ACCEPTED_REFRESH_MESSAGE,
      }),
    });
  });

  await page.route("**/api/refresh/status", async (route) => {
    refreshStatusRequests += 1;

    if (refreshStatusRequests === 1) {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          status: "processing",
          message: ACCEPTED_REFRESH_MESSAGE,
          started_at: "2026-03-11T10:00:00Z",
          finished_at: null,
          new_articles: 0,
          processed_articles: 0,
          failed_articles: 0,
        }),
      });
      return;
    }

    refreshFinished = true;

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        status: "completed",
        message: "Refresh completed.",
        started_at: "2026-03-11T10:00:00Z",
        finished_at: "2026-03-11T10:00:02Z",
        new_articles: 1,
        processed_articles: 1,
        failed_articles: 0,
      }),
    });
  });

  await page.goto("/");

  await expect(
    page.getByRole("heading", {
      level: 2,
      name: "Cached headline stays available while refresh runs",
    })
  ).toBeVisible();

  await page.getByRole("button", { name: "Refresh articles" }).click();

  await expect(page.getByText("Refresh complete", { exact: true })).toBeVisible();
  await expect(page.getByText("Processed 1 new article.", { exact: true })).toBeVisible();
  await expect(
    page.getByRole("heading", {
      level: 2,
      name: "Fresh article arrives after refresh completes",
    })
  ).toBeVisible();

  await page.getByRole("button", { name: "Settings" }).click();
  await expect(
    page.getByText("Your saved NewsAPI key was accepted during the last refresh.")
  ).toBeVisible();
  expect(refreshStatusRequests).toBe(2);
});

test("surfaces invalid-key feedback without polling refresh status", async ({
  page,
}) => {
  let refreshStatusCalled = false;

  await saveApiKey(page, "invalid-key");
  await mockHomeData(page, () => [cachedArticle]);

  await page.route("**/api/refresh", async (route) => {
    await route.fulfill({
      status: 401,
      contentType: "application/json",
      body: JSON.stringify({
        detail: {
          code: "invalid_api_key",
          message: "Invalid API key. Check your key in Settings.",
        },
      }),
    });
  });

  await page.route("**/api/refresh/status", async (route) => {
    refreshStatusCalled = true;
    await route.fulfill({
      status: 500,
      contentType: "application/json",
      body: JSON.stringify({ detail: "unexpected polling call" }),
    });
  });

  await page.goto("/");
  await page.getByRole("button", { name: "Refresh articles" }).click();

  await expect(page.getByRole("heading", { level: 2, name: "Settings" })).toBeVisible();
  await expect(
    page.getByText("The saved NewsAPI key was rejected. Update it in Settings and try again.")
  ).toBeVisible();
  await expect(page.getByText("Refresh failed")).toBeVisible();
  await expect(page.getByText("Invalid API key. Check your key in Settings.")).toBeVisible();
  expect(refreshStatusCalled).toBe(false);
});

test("attaches to an in-progress refresh and waits for the shared terminal state", async ({
  page,
}) => {
  let refreshStatusRequests = 0;

  await saveApiKey(page, "valid-key");
  await mockHomeData(page, () => [cachedArticle]);

  await page.route("**/api/refresh", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        status: "processing",
        message: DUPLICATE_REFRESH_MESSAGE,
      }),
    });
  });

  await page.route("**/api/refresh/status", async (route) => {
    refreshStatusRequests += 1;

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(
        refreshStatusRequests === 1
          ? {
              status: "processing",
              message: ACCEPTED_REFRESH_MESSAGE,
              started_at: "2026-03-11T10:00:00Z",
              finished_at: null,
              new_articles: 0,
              processed_articles: 0,
              failed_articles: 0,
            }
          : {
              status: "completed",
              message: "Refresh completed.",
              started_at: "2026-03-11T10:00:00Z",
              finished_at: "2026-03-11T10:00:02Z",
              new_articles: 0,
              processed_articles: 0,
              failed_articles: 0,
            }
      ),
    });
  });

  await page.goto("/");
  await page.getByRole("button", { name: "Refresh articles" }).click();

  await expect(page.getByText("Refresh already running")).toBeVisible();
  await expect(
    page.getByText("Another refresh request is already in progress. Waiting for its final status now.")
  ).toBeVisible();
  await expect(page.getByText("Refresh finished", { exact: true })).toBeVisible();
  await expect(
    page.getByText("The in-progress refresh finished without adding new articles.")
  ).toBeVisible();

  await page.getByRole("button", { name: "Settings" }).click();
  await expect(
    page.getByText("Your saved NewsAPI key was accepted during the last refresh.")
  ).toHaveCount(0);
  expect(refreshStatusRequests).toBe(2);
});

test("shows a non-fatal timeout toast when polling stays in processing past 120 seconds", async ({
  page,
}) => {
  let refreshStatusRequests = 0;

  await page.clock.install({ time: new Date("2026-03-11T10:00:00Z") });
  await saveApiKey(page, "slow-key");
  await mockHomeData(page, () => [cachedArticle]);

  await page.route("**/api/refresh", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        status: "processing",
        message: ACCEPTED_REFRESH_MESSAGE,
      }),
    });
  });

  await page.route("**/api/refresh/status", async (route) => {
    refreshStatusRequests += 1;
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        status: "processing",
        message: ACCEPTED_REFRESH_MESSAGE,
        started_at: "2026-03-11T10:00:00Z",
        finished_at: null,
        new_articles: 0,
        processed_articles: 0,
        failed_articles: 0,
      }),
    });
  });

  await page.goto("/");
  await page.getByRole("button", { name: "Refresh articles" }).click();
  await expect.poll(() => refreshStatusRequests).toBeGreaterThan(0);

  await page.clock.runFor("02:01");

  await expect(page.getByText("Refresh still running")).toBeVisible();
  await expect(
    page.getByText(
      "The backend is still processing articles. You can keep browsing cached articles and check back shortly."
    )
  ).toBeVisible();
  await expect(
    page.getByRole("heading", {
      level: 2,
      name: "Cached headline stays available while refresh runs",
    })
  ).toBeVisible();
  await expect(page.getByRole("button", { name: "Refresh articles" })).toBeEnabled();
  expect(refreshStatusRequests).toBeGreaterThan(100);
});
