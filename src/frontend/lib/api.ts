import type {
  ArticleListResponse,
  Article,
  CategoriesResponse,
  ComparisonAnalysis,
  ComparisonResponse,
  GuardrailsResponse,
  HistoricalStatsResponse,
  SourcesResponse,
  StatsResponse,
  RefreshErrorCode,
  RefreshErrorResponse,
  RefreshResponse,
  RefreshStatusResponse,
} from "@/types/article";

interface FetchArticlesParams {
  page?: number;
  per_page?: number;
  good_news_only?: boolean;
  source?: string;
  category?: string;
  country?: string;
  search?: string;
}

export class RefreshRequestError extends Error {
  readonly status: number;
  readonly code: RefreshErrorCode | "unknown";

  constructor({
    status,
    code,
    message,
  }: {
    status: number;
    code: RefreshErrorCode | "unknown";
    message: string;
  }) {
    super(message);
    this.name = "RefreshRequestError";
    this.status = status;
    this.code = code;
  }
}

export class ApiRequestError extends Error {
  readonly status: number;

  constructor({ status, message }: { status: number; message: string }) {
    super(message);
    this.name = "ApiRequestError";
    this.status = status;
  }
}

function isRefreshErrorResponse(value: unknown): value is RefreshErrorResponse {
  if (!value || typeof value !== "object" || !("detail" in value)) {
    return false;
  }

  const detail = (value as RefreshErrorResponse).detail;
  return Boolean(
    detail &&
      typeof detail === "object" &&
      typeof detail.code === "string" &&
      typeof detail.message === "string"
  );
}

async function buildRefreshError(res: Response): Promise<RefreshRequestError> {
  const body = await res.json().catch(() => null);

  if (isRefreshErrorResponse(body)) {
    return new RefreshRequestError({
      status: res.status,
      code: body.detail.code,
      message: body.detail.message,
    });
  }

  return new RefreshRequestError({
    status: res.status,
    code: "unknown",
    message: `Refresh failed: ${res.status}`,
  });
}

export async function fetchArticles(
  params: FetchArticlesParams = {}
): Promise<ArticleListResponse> {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.set("page", String(params.page));
  if (params.per_page) searchParams.set("per_page", String(params.per_page));
  if (params.good_news_only) searchParams.set("good_news_only", "true");
  if (params.source) searchParams.set("source", params.source);
  if (params.category) searchParams.set("category", params.category);
  if (params.country) searchParams.set("country", params.country);
  if (params.search) searchParams.set("search", params.search);

  const res = await fetch(`/api/articles?${searchParams.toString()}`);
  if (!res.ok) throw new Error(`Failed to fetch articles: ${res.status}`);
  return res.json();
}

export async function fetchArticle(id: string): Promise<Article> {
  const res = await fetch(`/api/articles/${id}`);
  if (!res.ok) {
    throw new ApiRequestError({
      status: res.status,
      message: `Failed to fetch article: ${res.status}`,
    });
  }
  return res.json();
}

export async function fetchSources(): Promise<SourcesResponse> {
  const res = await fetch("/api/sources");
  if (!res.ok) throw new Error(`Failed to fetch sources: ${res.status}`);
  return res.json();
}

export async function fetchCategories(): Promise<CategoriesResponse> {
  const res = await fetch("/api/categories");
  if (!res.ok) throw new Error(`Failed to fetch categories: ${res.status}`);
  return res.json();
}

export async function fetchStats(): Promise<StatsResponse> {
  const res = await fetch("/api/stats");
  if (!res.ok) throw new Error(`Failed to fetch stats: ${res.status}`);
  return res.json();
}

export async function fetchHistoricalStats(
  days = 30
): Promise<HistoricalStatsResponse> {
  const res = await fetch(`/api/stats/historical?days=${days}`);
  if (!res.ok) {
    throw new Error(`Failed to fetch historical stats: ${res.status}`);
  }
  return res.json();
}

export async function refreshArticles(
  apiKey: string
): Promise<RefreshResponse> {
  const res = await fetch("/api/refresh", {
    method: "POST",
    headers: { "X-News-Api-Key": apiKey },
  });
  if (!res.ok) {
    throw await buildRefreshError(res);
  }
  return res.json();
}

export async function fetchRefreshStatus(): Promise<RefreshStatusResponse> {
  const res = await fetch("/api/refresh/status");
  if (!res.ok) throw new Error(`Failed to fetch refresh status: ${res.status}`);
  return res.json();
}

export async function fetchComparisonGroups(): Promise<ComparisonResponse> {
  const res = await fetch("/api/comparison");
  if (!res.ok) throw new Error(`Failed to fetch comparison groups: ${res.status}`);
  return res.json();
}

export async function analyseComparisonGroup(
  articleIds: string[]
): Promise<ComparisonAnalysis> {
  const res = await fetch("/api/comparison/analyse", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ article_ids: articleIds }),
  });
  if (!res.ok) throw new Error(`Failed to analyse comparison group: ${res.status}`);
  return res.json();
}

export async function fetchGuardrails(): Promise<GuardrailsResponse> {
  const res = await fetch("/api/settings/guardrails");
  if (!res.ok) throw new Error(`Failed to fetch guardrails: ${res.status}`);
  return res.json();
}

export async function updateGuardrails(
  keywords: string[]
): Promise<GuardrailsResponse> {
  const res = await fetch("/api/settings/guardrails", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ keywords }),
  });
  if (!res.ok) throw new Error(`Failed to update guardrails: ${res.status}`);
  return res.json();
}
