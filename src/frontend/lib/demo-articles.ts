/**
 * Detect seed/demo articles inserted by seed_manual_integration_data.
 *
 * Seed article IDs are always "manual-seed-###" (set in
 * src/backend/scripts/seed_manual_integration_data.py). No other caller
 * uses that prefix, so we key off it here instead of adding an `is_demo`
 * column to the Article model.
 */
export function isDemoArticle(article: { id: string }): boolean {
  return article.id.startsWith("manual-seed-");
}

/** Label shown in place of the "Read Full Article" link on demo rows. */
export const DEMO_ARTICLE_LABEL =
  "Demo article — add your NewsAPI key for live stories";
