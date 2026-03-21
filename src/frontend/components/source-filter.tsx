"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { Source } from "@/types/article";

interface SourceFilterProps {
  sources: Source[];
  value: string;
  onValueChange: (value: string) => void;
}

export function SourceFilter({
  sources,
  value,
  onValueChange,
}: SourceFilterProps) {
  return (
    <Select value={value} onValueChange={onValueChange}>
      <SelectTrigger className="w-[180px]" aria-label="Filter by source">
        <SelectValue placeholder="All Sources" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="all">All Sources</SelectItem>
        {sources.map((source) => (
          <SelectItem key={source.source_name} value={source.source_name}>
            {source.source_name} ({source.article_count})
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
