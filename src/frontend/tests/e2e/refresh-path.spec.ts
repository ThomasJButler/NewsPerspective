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
  source_name: string | null;
  source_id: string | null;
  author: string | null;
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

const followUpArticle: TestArticle = {
  id: "follow-up-story",
  original_title: "Fresh News follow-up adds context to the refresh",
  rewritten_title: "Fresh News follow-up adds context to the refresh",
  tldr: "Duplicate source rows should collapse into one source-filter option with a count.",
  original_description: null,
  source_name: "Fresh News",
  source_id: "fresh-news",
  author: "Morgan Patel",
  url: "https://example.com/follow-up-story",
  image_url: null,
  published_at: "2026-03-11T09:30:00Z",
  fetched_at: "2026-03-11T10:05:00Z",
  was_rewritten: true,
  original_sentiment: "positive",
  sentiment_score: 0.4,
  is_good_news: true,
  category: "science",
  processing_status: "processed",
};

const wireArticle: TestArticle = {
  id: "wire-story",
  original_title: "Wire update rounds out the refreshed feed",
  rewritten_title: null,
  tldr: "The refreshed feed can include multiple sources after one completed refresh.",
  original_description: null,
  source_name: "Wire Daily",
  source_id: "wire-daily",
  author: "Sam Rivera",
  url: "https://example.com/wire-story",
  image_url: null,
  published_at: "2026-03-11T11:15:00Z",
  fetched_at: "2026-03-11T10:02:00Z",
  was_rewritten: false,
  original_sentiment: "neutral",
  sentiment_score: 0.1,
  is_good_news: false,
  category: "general",
  processing_status: "processed",
};

const refreshedArticles = [refreshedArticle, followUpArticle, wireArticle];

function buildArticleListResponse(articles: TestArticle[]) {
  return {
    articles,
    total: articles.length,
    page: 1,
    per_page: 20,
    has_more: false,
  };
}

function cleanSourceValue(value: string | null) {
  const cleaned = value?.trim();
  return cleaned ? cleaned : null;
}

function getNormalizedSourceName(article: TestArticle) {
  return (
    cleanSourceValue(article.source_name) ??
    cleanSourceValue(article.source_id) ??
    "Unknown source"
  );
}

function buildSourcesResponse(articles: TestArticle[]) {
  const aggregatedSources = new Map<
    string,
    { source_name: string; source_id: string; article_count: number }
  >();

  for (const article of articles) {
    const sourceName = getNormalizedSourceName(article);
    const sourceId = cleanSourceValue(article.source_id) ?? "";
    const existingSource = aggregatedSources.get(sourceName);

    if (existingSource) {
      existingSource.article_count += 1;
      if (sourceId > existingSource.source_id) {
        existingSource.source_id = sourceId;
      }
      continue;
    }

    aggregatedSources.set(sourceName, {
      source_name: sourceName,
      source_id: sourceId,
      article_count: 1,
    });
  }

  const sources = Array.from(aggregatedSources.values()).sort(
    (left, right) =>
      right.article_count - left.article_count ||
      left.source_name.localeCompare(right.source_name)
  );

  return { sources };
}

function buildStatsResponse(articles: TestArticle[]) {
  const latestFetch = articles.reduce<string | null>((latest, article) => {
    if (!article.fetched_at) {
      return latest;
    }
    if (latest === null || article.fetched_at > latest) {
      return article.fetched_at;
    }
    return latest;
  }, null);

  return {
    total_articles: articles.length,
    rewritten_count: articles.filter((article) => article.was_rewritten).length,
    good_news_count: articles.filter((article) => article.is_good_news).length,
    sources_count: new Set(articles.map(getNormalizedSourceName)).size,
    latest_fetch: latestFetch,
  };
}

function buildRefreshStatusResponse(
  status: "processing" | "completed" | "failed",
  overrides: Partial<{
    message: string;
    started_at: string | null;
    finished_at: string | null;
    new_articles: number;
    processed_articles: number;
    failed_articles: number;
  }> = {}
) {
  const message =
    status === "processing"
      ? ACCEPTED_REFRESH_MESSAGE
      : status === "completed"
        ? "Refresh completed."
        : "Refresh failed.";

  return {
    status,
    message,
    started_at: "2026-03-11T10:00:00Z",
    finished_at: status === "processing" ? null : "2026-03-11T10:00:02Z",
    new_articles: 0,
    processed_articles: 0,
    failed_articles: 0,
    ...overrides,
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
  let refreshStarted = false;

  await saveApiKey(page, "valid-key");
  await mockHomeData(page, () => (refreshFinished ? refreshedArticles : [cachedArticle]));

  await page.route("**/api/refresh", async (route) => {
    refreshStarted = true;
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
    if (!refreshStarted) {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          status: "idle",
          message: "No refresh has been started yet.",
          started_at: null,
          finished_at: null,
          new_articles: 0,
          processed_articles: 0,
          failed_articles: 0,
        }),
      });
      return;
    }

    if (!refreshFinished) {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(buildRefreshStatusResponse("processing")),
      });
      refreshFinished = true;
      return;
    }

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(
        buildRefreshStatusResponse("completed", {
          new_articles: refreshedArticles.length,
          processed_articles: refreshedArticles.length,
        })
      ),
    });
  });

  await page.goto("/");

  await expect(
    page.getByRole("heading", {
      level: 2,
      name: "Cached headline stays available while refresh runs",
    })
  ).toBeVisible();
  await expect(page.getByText("Last refreshed", { exact: false })).toBeVisible();

  await page.getByRole("button", { name: "Refresh articles" }).click();

  await expect(page.getByText("Refresh complete", { exact: true })).toBeVisible();
  await expect(page.getByText("Processed 3 new articles.", { exact: true })).toBeVisible();
  await expect(
    page.getByText("Latest refresh added 3 articles.", { exact: true })
  ).toBeVisible();
  await expect(
    page.getByRole("heading", {
      level: 2,
      name: "Fresh article arrives after refresh completes",
    })
  ).toBeVisible();
  await expect(page.getByText("3 articles processed · 1 headline improved")).toBeVisible();

  await page.getByRole("combobox").click();
  await expect(page.getByRole("option", { name: "Fresh News (2)" })).toBeVisible();
  await expect(page.getByRole("option", { name: "Wire Daily (1)" })).toBeVisible();
  await page.keyboard.press("Escape");

  await page.getByRole("button", { name: "Settings" }).click();
  await expect(
    page.getByText("Your saved NewsAPI key was accepted during the last refresh.")
  ).toBeVisible();
});

test("surfaces invalid-key feedback without polling refresh status", async ({
  page,
}) => {
  let refreshStatusCalls = 0;

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
    refreshStatusCalls += 1;
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        status: "idle",
        message: "No refresh has been started yet.",
        started_at: null,
        finished_at: null,
        new_articles: 0,
        processed_articles: 0,
        failed_articles: 0,
      }),
    });
  });

  await page.goto("/");
  await expect.poll(() => refreshStatusCalls).toBe(1);
  await page.getByRole("button", { name: "Refresh articles" }).click();

  await expect(page.getByRole("heading", { level: 2, name: "Settings" })).toBeVisible();
  await expect(
    page.getByText("The saved NewsAPI key was rejected. Update it in Settings and try again.")
  ).toBeVisible();
  await expect(page.getByText("Refresh failed")).toBeVisible();
  await expect(page.getByText("Invalid API key. Check your key in Settings.")).toBeVisible();
  expect(refreshStatusCalls).toBe(1);
});

test("attaches to an in-progress refresh and waits for the shared terminal state", async ({
  page,
}) => {
  let refreshStatusRequests = 0;
  let refreshStarted = false;

  await saveApiKey(page, "valid-key");
  await mockHomeData(page, () => [cachedArticle]);

  await page.route("**/api/refresh", async (route) => {
    refreshStarted = true;
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
    if (!refreshStarted) {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          status: "idle",
          message: "No refresh has been started yet.",
          started_at: null,
          finished_at: null,
          new_articles: 0,
          processed_articles: 0,
          failed_articles: 0,
        }),
      });
      return;
    }

    refreshStatusRequests += 1;

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(
        refreshStatusRequests === 1
          ? buildRefreshStatusResponse("processing")
          : buildRefreshStatusResponse("completed")
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
});

test("shows a non-fatal timeout toast when polling stays in processing past 120 seconds", async ({
  page,
}) => {
  let refreshStatusRequests = 0;
  let refreshStarted = false;

  await page.clock.install({ time: new Date("2026-03-11T10:00:00Z") });
  await saveApiKey(page, "slow-key");
  await mockHomeData(page, () => [cachedArticle]);

  await page.route("**/api/refresh", async (route) => {
    refreshStarted = true;
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
    if (!refreshStarted) {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          status: "idle",
          message: "No refresh has been started yet.",
          started_at: null,
          finished_at: null,
          new_articles: 0,
          processed_articles: 0,
          failed_articles: 0,
        }),
      });
      return;
    }

    refreshStatusRequests += 1;
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(buildRefreshStatusResponse("processing")),
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

  const requestsWhenTimeoutToastAppeared = refreshStatusRequests;
  await page.clock.runFor("00:05");
  expect(refreshStatusRequests).toBe(requestsWhenTimeoutToastAppeared);
});

test("keeps the last successful refresh visible after the backend tracker resets to idle", async ({
  page,
}) => {
  await saveApiKey(page, "valid-key");
  await mockHomeData(page, () => refreshedArticles);

  await page.route("**/api/refresh/status", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        status: "idle",
        message: "No refresh has been started yet.",
        started_at: null,
        finished_at: null,
        new_articles: 0,
        processed_articles: 0,
        failed_articles: 0,
      }),
    });
  });

  await page.goto("/");

  await expect(page.getByText("Ready to refresh", { exact: true })).toBeVisible();
  await expect(page.getByText("Last refreshed", { exact: false })).toBeVisible();
  await expect(
    page.getByText(
      "No refresh is running. Cached headlines still reflect the latest successful fetch."
    )
  ).toBeVisible();
});
