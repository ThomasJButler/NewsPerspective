export interface Article {
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
  published_at: string | null;
  fetched_at: string | null;
  was_rewritten: boolean;
  original_sentiment: string | null;
  sentiment_score: number | null;
  is_good_news: boolean;
  category: string | null;
  country: string;
  processing_status: string;
}

export interface ArticleListResponse {
  articles: Article[];
  total: number;
  page: number;
  per_page: number;
  has_more: boolean;
}

export interface Source {
  source_name: string;
  source_id: string;
  article_count: number;
}

export interface SourcesResponse {
  sources: Source[];
}

export interface Category {
  name: string;
  count: number;
}

export interface CategoriesResponse {
  categories: Category[];
}

export interface StatsResponse {
  total_articles: number;
  rewritten_count: number;
  good_news_count: number;
  sources_count: number;
  latest_fetch: string | null;
}

export interface DailyArticleCount {
  date: string;
  count: number;
}

export interface DailyRewriteRate {
  date: string;
  total: number;
  rewritten: number;
  rate: number;
}

export interface SentimentMix {
  positive: number;
  neutral: number;
  negative: number;
}

export interface HistoricalStatsResponse {
  days: number;
  articles_over_time: DailyArticleCount[];
  rewrite_rate: DailyRewriteRate[];
  sentiment_mix: SentimentMix;
}

export interface RefreshResponse {
  status: string;
  message: string;
}

export type RefreshStatus = "idle" | "processing" | "completed" | "failed";

export type RefreshErrorCode =
  | "missing_api_key"
  | "invalid_api_key"
  | "upstream_timeout"
  | "upstream_transport_failure";

export interface RefreshErrorDetail {
  code: RefreshErrorCode;
  message: string;
}

export interface RefreshErrorResponse {
  detail: RefreshErrorDetail;
}

export interface RefreshStatusResponse {
  status: RefreshStatus;
  message: string;
  started_at: string | null;
  finished_at: string | null;
  new_articles: number;
  processed_articles: number;
  failed_articles: number;
}

export interface ComparisonArticleSummary {
  id: string;
  original_title: string;
  rewritten_title: string | null;
  source_name: string | null;
  country: string;
  original_sentiment: string | null;
  sentiment_score: number | null;
  url: string;
  image_url: string | null;
  published_at: string | null;
}

export interface ComparisonGroup {
  representative_title: string;
  articles: ComparisonArticleSummary[];
  sources: string[];
  countries: string[];
}

export interface ComparisonResponse {
  groups: ComparisonGroup[];
  total_groups: number;
}

export interface ComparisonSourceTone {
  source_name: string;
  country: string;
  tone: string;
}

export interface ComparisonAnalysis {
  representative_title: string;
  summary: string;
  framing_differences: string[];
  source_tones: ComparisonSourceTone[];
}

export interface GuardrailsResponse {
  keywords: string[];
}
