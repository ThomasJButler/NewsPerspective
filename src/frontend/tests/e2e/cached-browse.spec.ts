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
  await expect(page.getByText(/articles processed/)).toBeVisible();

  await captureScreenshot(page, testInfo, "cached-browse-home.png");
});

test("filters seeded cached articles and opens article detail", async ({ page }, testInfo) => {
  await page.goto("/");

  await page.getByRole("combobox").click();
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
  const sourceFilter = page.getByRole("combobox");
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
      body: JSON.stringify({
        articles: [stubbedArticle],
        total: 1,
        page: 1,
        per_page: 20,
        has_more: false,
      }),
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
