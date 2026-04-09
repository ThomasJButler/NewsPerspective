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
      />
      <label
        htmlFor="good-news-toggle"
        className="flex items-center gap-1.5 text-sm font-medium cursor-pointer select-none whitespace-nowrap"
      >
        <Sparkles
          className={`h-3.5 w-3.5 transition-colors ${
            checked ? "text-brand" : "text-muted-foreground"
          }`}
          aria-hidden="true"
        />
        Good News Only
      </label>
    </div>
  );
}
