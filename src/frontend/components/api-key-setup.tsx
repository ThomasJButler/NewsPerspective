"use client";

import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

interface ApiKeySetupProps {
  onSubmit: (key: string) => void;
}

export function ApiKeySetup({ onSubmit }: ApiKeySetupProps) {
  const [key, setKey] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (key.trim()) {
      onSubmit(key.trim());
    }
  };

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
