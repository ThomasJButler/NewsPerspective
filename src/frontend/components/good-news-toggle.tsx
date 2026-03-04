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
    <div className="flex items-center gap-2">
      <Switch
        id="good-news-toggle"
        checked={checked}
        onCheckedChange={onCheckedChange}
      />
      <label
        htmlFor="good-news-toggle"
        className="text-sm font-medium cursor-pointer select-none"
      >
        Good News Only
      </label>
    </div>
  );
}
