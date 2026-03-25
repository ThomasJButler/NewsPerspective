import { expect, test, type Page, type TestInfo } from "@playwright/test";

async function captureScreenshot(
  page: Page,
  testInfo: TestInfo,
  name: string
) {
  await page.screenshot({
    path: testInfo.outputPath(name),
    fullPage: true,
    animations: "disabled",
  });
}

const stubbedArticle = {
  id: "fallback-story",
  original_title: "Original headline stays visible when rewrite output is blank",
  rewritten_title: "",
  tldr: "A rewritten headline can fail validation. The UI should still render a readable title.",
  original_description: null,
  source_name: "Fallback News",
  source_id: "fallback-news",
  author: "Casey Chen",
  url: "https://example.com/fallback-story",
  image_url: null,
  published_at: "2026-03-09T12:00:00Z",
  fetched_at: "2026-03-09T12:00:00Z",
  was_rewritten: true,
  original_sentiment: "neutral",
  sentiment_score: 0,
  is_good_news: false,
  category: "general",
  processing_status: "processed",
};

type TestArticle = Omit<typeof stubbedArticle, "rewritten_title" | "tldr"> & {
  rewritten_title: string | null;
  tldr: string | null;
};

function buildArticle(overrides: Partial<TestArticle> = {}): TestArticle {
  return {
    ...stubbedArticle,
    rewritten_title: null,
    tldr: "Stubbed article summary for deterministic frontend coverage.",
    was_rewritten: false,
    ...overrides,
  };
}

function buildArticleListResponse(
  articleOrArticles: TestArticle | TestArticle[] = stubbedArticle
) {
  const articles = Array.isArray(articleOrArticles)
    ? articleOrArticles
    : [articleOrArticles];

  return {
    articles,
    total: articles.length,
    page: 1,
    per_page: 20,
    has_more: false,
  };
}

test("shows seeded cached articles without a saved key", async ({ page }, testInfo) => {
  await page.goto("/");

  await expect(
    page.getByRole("heading", { level: 1, name: "NewsPerspective" })
  ).toBeVisible();
  await expect(page.getByText("Fetch fresh headlines")).toBeVisible();
  await expect(
    page.getByText(
      "Browse cached articles below. Add your NewsAPI key to refresh the feed with new stories."
    )
  ).toBeVisible();
  await expect(
    page.getByRole("heading", {
      level: 2,
      name: "NHS expands virtual wards to ease hospital demand",
    })
  ).toBeVisible();
  await expect(
    page.getByText("Excludes sports, entertainment, politics, and distressing content.")
  ).toBeVisible();
  await expect(page.getByText(/articles processed/)).toBeVisible();

  await captureScreenshot(page, testInfo, "cached-browse-home.png");
});

test("refreshes the feed and metadata immediately after saving blocked topics", async ({
  page,
}) => {
  const visibleArticle = buildArticle({
    id: "visible-story",
    original_title: "Community garden opens new plots for families",
    source_name: "Local News",
    source_id: "local-news",
    url: "https://example.com/visible-story",
    category: "general",
  });
  const blockedArticle = buildArticle({
    id: "blocked-story",
    original_title: "Climate change plan draws broad support",
    source_name: "Climate Desk",
    source_id: "climate-desk",
    url: "https://example.com/blocked-story",
    category: "science",
  });

  let blockedTopics: string[] = [];

  function getCurrentArticles() {
    return blockedTopics.includes("climate")
      ? [visibleArticle]
      : [visibleArticle, blockedArticle];
  }

  function buildSourcesResponse(articles: TestArticle[]) {
    const counts = new Map<string, { source_name: string; source_id: string; article_count: number }>();

    for (const article of articles) {
      const sourceName = article.source_name ?? "Unknown source";
      const sourceId = article.source_id ?? "";
      const existing = counts.get(sourceName);

      if (existing) {
        existing.article_count += 1;
        continue;
      }

      counts.set(sourceName, {
        source_name: sourceName,
        source_id: sourceId,
        article_count: 1,
      });
    }

    return {
      sources: Array.from(counts.values()).sort((left, right) =>
        left.source_name.localeCompare(right.source_name)
      ),
    };
  }

  function buildCategoriesResponse(articles: TestArticle[]) {
    const counts = new Map<string, number>();

    for (const article of articles) {
      const category = article.category ?? "general";
      counts.set(category, (counts.get(category) ?? 0) + 1);
    }

    return {
      categories: Array.from(counts.entries())
        .map(([name, count]) => ({ name, count }))
        .sort((left, right) => left.name.localeCompare(right.name)),
    };
  }

  function buildStatsResponse(articles: TestArticle[]) {
    return {
      total_articles: articles.length,
      rewritten_count: articles.filter((article) => article.was_rewritten).length,
      good_news_count: articles.filter((article) => article.is_good_news).length,
      sources_count: new Set(
        articles.map((article) => article.source_name ?? "Unknown source")
      ).size,
      latest_fetch: "2026-03-09T12:00:00Z",
    };
  }

  await page.route("**/api/articles?**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(buildArticleListResponse(getCurrentArticles())),
    });
  });

  await page.route("**/api/sources", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(buildSourcesResponse(getCurrentArticles())),
    });
  });

  await page.route("**/api/categories", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(buildCategoriesResponse(getCurrentArticles())),
    });
  });

  await page.route("**/api/stats", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(buildStatsResponse(getCurrentArticles())),
    });
  });

  await page.route("**/api/refresh/status", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        status: "idle",
        message: "Idle.",
        started_at: null,
        finished_at: null,
        new_articles: 0,
        processed_articles: 0,
        failed_articles: 0,
      }),
    });
  });

  await page.route("**/api/settings/guardrails", async (route) => {
    if (route.request().method() === "PUT") {
      const body = route.request().postDataJSON() as { keywords: string[] };
      blockedTopics = body.keywords;
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ keywords: blockedTopics }),
      });
      return;
    }

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ keywords: blockedTopics }),
    });
  });

  await page.goto("/");

  await expect(
    page.getByRole("heading", { level: 2, name: visibleArticle.original_title })
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { level: 2, name: blockedArticle.original_title })
  ).toBeVisible();
  await expect(page.getByText("2 articles processed · 0 headlines improved")).toBeVisible();

  await page.getByRole("button", { name: "Settings" }).click();
  await expect(page.getByRole("dialog", { name: "Settings" })).toBeVisible();
  await page.getByRole("textbox", { name: "New blocked keyword" }).fill("climate");
  await page.getByRole("button", { name: "Add blocked topic" }).click();

  await expect(page.getByText("climate")).toBeVisible();
  await expect(
    page.getByRole("heading", { level: 2, name: blockedArticle.original_title })
  ).toHaveCount(0);
  await expect(page.getByText("1 article processed · 0 headlines improved")).toBeVisible();
  await page.getByRole("button", { name: "Close settings" }).click();

  await page.getByRole("combobox", { name: "Filter by source" }).click();
  await expect(page.getByRole("option", { name: /Local News/ })).toBeVisible();
  await expect(page.getByRole("option", { name: /Climate Desk/ })).toHaveCount(0);
  await page.keyboard.press("Escape");

  await page.getByRole("combobox", { name: "Filter by category" }).click();
  await expect(page.getByRole("option", { name: /General \(1\)/ })).toBeVisible();
  await expect(page.getByRole("option", { name: /Science/ })).toHaveCount(0);
});

test("filters seeded cached articles and opens article detail", async ({ page }, testInfo) => {
  await page.goto("/");

  await page.getByRole("combobox", { name: "Filter by source" }).click();
  await page.getByRole("option", { name: /Reuters/ }).click();

  await expect(page).toHaveURL(/source=Reuters/);
  await expect(
    page.getByRole("heading", {
      level: 2,
      name: "Port strike talks resume as exporters seek clarity",
    })
  ).toBeVisible();
  await expect(
    page.getByRole("heading", {
      level: 2,
      name: "NHS expands virtual wards to ease hospital demand",
    })
  ).toHaveCount(0);

  await page.getByRole("searchbox", { name: "Search articles" }).fill("solar farm");

  await expect(page).toHaveURL(/search=solar(\+|%20)farm/);

  const detailLink = page.getByRole("heading", {
    level: 2,
    name: "UK approves solar farm planned to supply 120,000 homes",
  });

  await expect(detailLink).toBeVisible();
  await expect(
    page.getByRole("heading", {
      level: 2,
      name: "Port strike talks resume as exporters seek clarity",
    })
  ).toHaveCount(0);

  await captureScreenshot(page, testInfo, "cached-browse-filtered-results.png");

  await detailLink.click();

  await expect(page).toHaveURL(/\/article\//);
  await expect(
    page.getByRole("heading", {
      level: 1,
      name: "UK approves solar farm planned to supply 120,000 homes",
    })
  ).toBeVisible();
  await expect(page.getByText("Reuters")).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Read Full Article →" })
  ).toBeVisible();

  await captureScreenshot(page, testInfo, "cached-browse-article-detail.png");
});

test("keeps home-page controls in sync when browser history changes", async ({ page }) => {
  await page.goto("/");

  const goodNewsSwitch = page.getByRole("switch", { name: "Good News Only" });
  const sourceFilter = page.getByRole("combobox", { name: "Filter by source" });
  const searchBox = page.getByRole("searchbox", { name: "Search articles" });

  await goodNewsSwitch.click();
  await expect(page).toHaveURL(/good_news=true/);

  await sourceFilter.click();
  await page.getByRole("option", { name: /Reuters/ }).click();
  await expect(page).toHaveURL(/source=Reuters/);

  await searchBox.fill("solar farm");
  await expect(page).toHaveURL(/search=solar(\+|%20)farm/);
  await expect(searchBox).toHaveValue("solar farm");
  await expect(sourceFilter).toContainText("Reuters");
  await expect(goodNewsSwitch).toBeChecked();

  await page.goBack();
  await expect(page).not.toHaveURL(/search=solar(\+|%20)farm/);
  await expect(searchBox).toHaveValue("");
  await expect(sourceFilter).toContainText("Reuters");
  await expect(goodNewsSwitch).toBeChecked();

  await page.goBack();
  await expect(page).not.toHaveURL(/source=Reuters/);
  await expect(sourceFilter).toContainText("All Sources");
  await expect(goodNewsSwitch).toBeChecked();

  await page.goBack();
  await expect(page).not.toHaveURL(/good_news=true/);
  await expect(goodNewsSwitch).not.toBeChecked();
  await expect(
    page.getByRole("heading", {
      level: 2,
      name: "NHS expands virtual wards to ease hospital demand",
    })
  ).toBeVisible();
});

test("shows a retryable error state for transient article-detail failures", async ({
  page,
}) => {
  let detailRequestCount = 0;

  await page.route("**/api/articles/retryable-article", async (route) => {
    detailRequestCount += 1;

    if (detailRequestCount === 1) {
      await route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ detail: "temporary failure" }),
      });
      return;
    }

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(stubbedArticle),
    });
  });

  await page.goto("/article/retryable-article");

  await expect(
    page.getByRole("heading", { level: 1, name: "Unable to load article" })
  ).toBeVisible();
  await expect(
    page
      .getByRole("heading", { level: 1, name: "Unable to load article" })
      .locator("..")
  ).toContainText("Failed to fetch article: 500");
  await expect(
    page.getByRole("heading", { level: 1, name: "Article not found" })
  ).toHaveCount(0);

  await page.getByRole("button", { name: "Retry" }).click();

  await expect(
    page.getByRole("heading", {
      level: 1,
      name: "Original headline stays visible when rewrite output is blank",
    })
  ).toBeVisible();
});

test("falls back to the original headline when rewritten text is blank", async ({
  page,
}) => {
  await page.route("**/api/articles?**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(buildArticleListResponse(stubbedArticle)),
    });
  });

  await page.route("**/api/sources", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        sources: [
          {
            source_name: "Fallback News",
            source_id: "fallback-news",
            article_count: 1,
          },
        ],
      }),
    });
  });

  await page.route("**/api/stats", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        total_articles: 1,
        rewritten_count: 1,
        good_news_count: 0,
        sources_count: 1,
        latest_fetch: "2026-03-09T12:00:00Z",
      }),
    });
  });

  await page.goto("/");

  await expect(
    page.getByRole("heading", {
      level: 2,
      name: "Original headline stays visible when rewrite output is blank",
    })
  ).toBeVisible();
  await expect(page.getByText("Original headline", { exact: true })).toHaveCount(0);
});

test("keeps the newest search results when an older article response finishes later", async ({
  page,
}) => {
  const initialArticle = buildArticle({
    id: "initial-story",
    original_title: "Initial cached article",
    url: "https://example.com/initial-story",
  });
  const staleArticle = buildArticle({
    id: "stale-story",
    original_title: "Stale search result should not overwrite the feed",
    url: "https://example.com/stale-story",
  });
  const freshArticle = buildArticle({
    id: "fresh-story",
    original_title: "Fresh search result should stay visible",
    url: "https://example.com/fresh-story",
  });

  await page.route("**/api/articles?**", async (route) => {
    const url = new URL(route.request().url());
    const search = url.searchParams.get("search");

    if (search === "nhs") {
      await new Promise((resolve) => setTimeout(resolve, 2500));
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(buildArticleListResponse(staleArticle)),
      });
      return;
    }

    if (search === "solar") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(buildArticleListResponse(freshArticle)),
      });
      return;
    }

    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(buildArticleListResponse(initialArticle)),
    });
  });

  await page.goto("/");

  const searchBox = page.getByRole("searchbox", { name: "Search articles" });
  const staleHeading = page.getByRole("heading", {
    level: 2,
    name: "Stale search result should not overwrite the feed",
  });
  const freshHeading = page.getByRole("heading", {
    level: 2,
    name: "Fresh search result should stay visible",
  });

  await expect(
    page.getByRole("heading", { level: 2, name: "Initial cached article" })
  ).toBeVisible();

  const staleRequest = page.waitForRequest((request) => {
    const url = new URL(request.url());
    return (
      url.pathname === "/api/articles" &&
      url.searchParams.get("search") === "nhs"
    );
  });

  await searchBox.fill("nhs");
  await staleRequest;
  await expect(page).toHaveURL(/search=nhs/);

  await searchBox.fill("solar");

  await expect(page).toHaveURL(/search=solar/);
  await expect(freshHeading).toBeVisible();
  await expect(staleHeading).toHaveCount(0);

  await page.waitForTimeout(3000);

  await expect(freshHeading).toBeVisible();
  await expect(staleHeading).toHaveCount(0);
});
