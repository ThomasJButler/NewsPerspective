"use client";

import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

interface ApiKeySetupProps {
  onSubmit: (key: string) => void;
  variant?: "fullscreen" | "inline";
}

export function ApiKeySetup({
  onSubmit,
  variant = "fullscreen",
}: ApiKeySetupProps) {
  const [key, setKey] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (key.trim()) {
      onSubmit(key.trim());
    }
  };

  if (variant === "inline") {
    return (
      <Card className="border-dashed bg-muted/30">
        <CardHeader className="gap-1">
          <CardTitle>Fetch fresh headlines</CardTitle>
          <CardDescription>
            Browse cached articles below. Add your NewsAPI key to refresh the
            feed with new stories.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <form
            onSubmit={handleSubmit}
            className="flex flex-col gap-3 sm:flex-row sm:items-start"
          >
            <Input
              type="text"
              placeholder="Enter your News API key"
              value={key}
              onChange={(e) => setKey(e.target.value)}
              aria-label="News API key"
              className="sm:flex-1"
            />
            <Button type="submit" disabled={!key.trim()} className="sm:min-w-28">
              Save Key
            </Button>
          </form>
          <p className="text-xs text-muted-foreground">
            Free key from{" "}
            <a
              href="https://newsapi.org/register"
              target="_blank"
              rel="noopener noreferrer"
              className="underline hover:text-foreground"
            >
              newsapi.org/register
            </a>
            . Your key stays in your browser and is only sent to the backend
            when you ask to refresh.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="max-w-md w-full text-center space-y-6">
        <div>
          <h1 className="text-3xl font-bold">NewsPerspective</h1>
          <p className="text-muted-foreground mt-1">
            See the news. Not the spin.
          </p>
        </div>

        <p className="text-sm text-muted-foreground">
          News headlines are designed to grab your attention, not inform you. We
          fix that.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Input
              type="text"
              placeholder="Enter your News API key"
              value={key}
              onChange={(e) => setKey(e.target.value)}
              aria-label="News API key"
            />
            <Button type="submit" className="w-full" disabled={!key.trim()}>
              Get Started
            </Button>
          </div>
          <p className="text-xs text-muted-foreground">
            Free key →{" "}
            <a
              href="https://newsapi.org/register"
              target="_blank"
              rel="noopener noreferrer"
              className="underline hover:text-foreground"
            >
              newsapi.org/register
            </a>
          </p>
        </form>

        <p className="text-xs text-muted-foreground">
          Your key stays in your browser. We never store or share it.
        </p>
      </div>
    </div>
  );
}
