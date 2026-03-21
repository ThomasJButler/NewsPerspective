"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { Category } from "@/types/article";

interface CategoryFilterProps {
  categories: Category[];
  value: string;
  onValueChange: (value: string) => void;
}

export function CategoryFilter({
  categories,
  value,
  onValueChange,
}: CategoryFilterProps) {
  return (
    <Select value={value} onValueChange={onValueChange}>
      <SelectTrigger className="w-[180px]" aria-label="Filter by category">
        <SelectValue placeholder="All Categories" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="all">All Categories</SelectItem>
        {categories.map((category) => (
          <SelectItem key={category.name} value={category.name}>
            {category.name.charAt(0).toUpperCase() + category.name.slice(1)} ({category.count})
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
