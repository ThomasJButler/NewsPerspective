"use client";

import { Sparkles } from "lucide-react";
import { Switch } from "@/components/ui/switch";

interface GoodNewsToggleProps {
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
}

export function GoodNewsToggle({
  checked,
  onCheckedChange,
}: GoodNewsToggleProps) {
  return (
    <div
      className="flex items-center gap-2.5 shrink-0"
      title="Excludes sports, entertainment, politics, and distressing content."
    >
      <Switch
        id="good-news-toggle"
        checked={checked}
        onCheckedChange={onCheckedChange}
        aria-describedby="good-news-toggle-hint"
      />
      <label
        htmlFor="good-news-toggle"
        className="flex items-center gap-1.5 text-sm font-medium cursor-pointer select-none whitespace-nowrap"
      >
        Good News Only
      </label>
      {/*
        Visually hidden hint kept in the DOM so screen readers can describe
        what the toggle excludes. The native `title` tooltip above handles
        the sighted hover case; this span handles the assistive-tech case.
      */}
      <span id="good-news-toggle-hint" className="sr-only">
        Excludes sports, entertainment, politics, and distressing content.
      </span>
    </div>
  );
}
