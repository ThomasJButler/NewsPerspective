"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { fetchHistoricalStats } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import type { HistoricalStatsResponse } from "@/types/article";

const SENTIMENT_COLORS = {
  positive: "oklch(0.72 0.15 150)",
  neutral: "oklch(0.70 0.01 250)",
  negative: "oklch(0.60 0.22 27)",
} as const;

function formatShortDate(iso: string): string {
  // ECMAScript parses bare ISO date strings ("2026-04-09") as UTC midnight,
  // which shifts the rendered label one day earlier for users west of UTC.
  // Append a time component so the date is parsed in the user's local zone.
  const date = new Date(`${iso}T00:00:00`);
  return date.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
}

function ChartCard({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: React.ReactNode;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
        {description && (
          <p className="text-sm text-muted-foreground">{description}</p>
        )}
      </CardHeader>
      <CardContent>
        <div className="h-64 w-full">{children}</div>
      </CardContent>
    </Card>
  );
}

function LoadingCard({ title }: { title: string }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <Skeleton className="h-64 w-full" />
      </CardContent>
    </Card>
  );
}

export default function StatsPage() {
  const [data, setData] = useState<HistoricalStatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        setLoading(true);
        setError(null);
        const result = await fetchHistoricalStats(30);
        if (!cancelled) {
          setData(result);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load stats");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const hasData = data && data.articles_over_time.some((row) => row.count > 0);
  const sentimentMix = data?.sentiment_mix;
  const sentimentTotal = sentimentMix
    ? sentimentMix.positive + sentimentMix.neutral + sentimentMix.negative
    : 0;

  return (
    <div className="container mx-auto px-4 py-8 max-w-3xl space-y-6">
      <div className="space-y-1">
        <h1 className="text-3xl font-bold">Stats</h1>
        <p className="text-sm text-muted-foreground">
          30-day view of how NewsPerspective is processing your feed.
        </p>
      </div>

      {loading && (
        <div className="space-y-6">
          <LoadingCard title="Articles over time" />
          <LoadingCard title="Rewrite rate trend" />
          <LoadingCard title="Sentiment mix" />
        </div>
      )}

      {error && !loading && (
        <Card>
          <CardContent className="py-8 text-center space-y-3">
            <p className="text-sm text-destructive">
              Could not load stats: {error}
            </p>
            <Button variant="outline" asChild>
              <Link href="/">Back to feed</Link>
            </Button>
          </CardContent>
        </Card>
      )}

      {!loading && !error && !hasData && (
        <Card>
          <CardContent className="py-8 text-center space-y-3">
            <p className="text-sm text-muted-foreground">
              No processed articles yet. Add your NewsAPI key and refresh the
              feed to populate these charts.
            </p>
            <Button variant="outline" asChild>
              <Link href="/">Back to feed</Link>
            </Button>
          </CardContent>
        </Card>
      )}

      {!loading && !error && hasData && data && (
        <div className="space-y-6">
          <ChartCard
            title="Articles over time"
            description="Processed articles per day for the last 30 days."
          >
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={data.articles_over_time.map((row) => ({
                  ...row,
                  label: formatShortDate(row.date),
                }))}
                margin={{ top: 8, right: 8, left: 0, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                <XAxis
                  dataKey="label"
                  tick={{ fontSize: 12 }}
                  interval="preserveStartEnd"
                />
                <YAxis tick={{ fontSize: 12 }} allowDecimals={false} />
                <Tooltip
                  contentStyle={{
                    background: "var(--popover)",
                    border: "1px solid var(--border)",
                    borderRadius: "6px",
                    fontSize: "12px",
                  }}
                  labelStyle={{ color: "var(--foreground)" }}
                />
                <Line
                  type="monotone"
                  dataKey="count"
                  name="Articles"
                  stroke="var(--brand)"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard
            title="Rewrite rate trend"
            description="Percentage of headlines the AI decided to rewrite per day."
          >
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={data.rewrite_rate.map((row) => ({
                  label: formatShortDate(row.date),
                  percent: Math.round(row.rate * 1000) / 10,
                  total: row.total,
                  rewritten: row.rewritten,
                }))}
                margin={{ top: 8, right: 8, left: 0, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                <XAxis
                  dataKey="label"
                  tick={{ fontSize: 12 }}
                  interval="preserveStartEnd"
                />
                <YAxis
                  tick={{ fontSize: 12 }}
                  domain={[0, 100]}
                  tickFormatter={(value) => `${value}%`}
                />
                <Tooltip
                  contentStyle={{
                    background: "var(--popover)",
                    border: "1px solid var(--border)",
                    borderRadius: "6px",
                    fontSize: "12px",
                  }}
                  formatter={(value: number, _name, entry) => {
                    const row = entry.payload as {
                      rewritten: number;
                      total: number;
                    };
                    return [
                      `${value}% (${row.rewritten} of ${row.total})`,
                      "Rewrite rate",
                    ];
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="percent"
                  stroke="var(--brand)"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </ChartCard>

          <ChartCard
            title="Sentiment mix"
            description={`Current distribution across ${sentimentTotal} analysed articles.`}
          >
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={[
                    {
                      name: "Positive",
                      value: sentimentMix?.positive ?? 0,
                      fill: SENTIMENT_COLORS.positive,
                    },
                    {
                      name: "Neutral",
                      value: sentimentMix?.neutral ?? 0,
                      fill: SENTIMENT_COLORS.neutral,
                    },
                    {
                      name: "Negative",
                      value: sentimentMix?.negative ?? 0,
                      fill: SENTIMENT_COLORS.negative,
                    },
                  ]}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={90}
                  label={(entry: { name?: string; value?: number }) =>
                    `${entry.name ?? ""}: ${entry.value ?? 0}`
                  }
                >
                  {["positive", "neutral", "negative"].map((key) => (
                    <Cell
                      key={key}
                      fill={
                        SENTIMENT_COLORS[key as keyof typeof SENTIMENT_COLORS]
                      }
                    />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    background: "var(--popover)",
                    border: "1px solid var(--border)",
                    borderRadius: "6px",
                    fontSize: "12px",
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </ChartCard>
        </div>
      )}
    </div>
  );
}
