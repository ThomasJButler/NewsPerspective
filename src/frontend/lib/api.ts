import type {
  ArticleListResponse,
  Article,
  SourcesResponse,
  StatsResponse,
  RefreshResponse,
} from "@/types/article";

interface FetchArticlesParams {
  page?: number;
  per_page?: number;
  good_news_only?: boolean;
  source?: string;
  category?: string;
  search?: string;
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
  if (params.search) searchParams.set("search", params.search);

  const res = await fetch(`/api/articles?${searchParams.toString()}`);
  if (!res.ok) throw new Error(`Failed to fetch articles: ${res.status}`);
  return res.json();
}

export async function fetchArticle(id: string): Promise<Article> {
  const res = await fetch(`/api/articles/${id}`);
  if (!res.ok) throw new Error(`Failed to fetch article: ${res.status}`);
  return res.json();
}

export async function fetchSources(): Promise<SourcesResponse> {
  const res = await fetch("/api/sources");
  if (!res.ok) throw new Error(`Failed to fetch sources: ${res.status}`);
  return res.json();
}

export async function fetchStats(): Promise<StatsResponse> {
  const res = await fetch("/api/stats");
  if (!res.ok) throw new Error(`Failed to fetch stats: ${res.status}`);
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
    const body = await res.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(body.detail || `Refresh failed: ${res.status}`);
  }
  return res.json();
}
