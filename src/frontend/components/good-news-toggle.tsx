"use client";

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
    <div className="flex flex-col gap-1">
      <div className="flex items-center gap-2">
        <Switch
          id="good-news-toggle"
          checked={checked}
          onCheckedChange={onCheckedChange}
          aria-describedby="good-news-toggle-hint"
        />
        <label
          htmlFor="good-news-toggle"
          className="text-sm font-medium cursor-pointer select-none"
        >
          Good News Only
        </label>
      </div>
      <p
        id="good-news-toggle-hint"
        className="text-xs text-muted-foreground"
      >
        Excludes sports, entertainment, politics, and distressing content.
      </p>
    </div>
  );
}
