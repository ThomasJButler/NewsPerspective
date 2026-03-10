import { expect, test } from "@playwright/test";

test("shows seeded cached articles without a saved key", async ({ page }) => {
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
});

test("filters seeded cached articles and opens article detail", async ({ page }) => {
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
});
