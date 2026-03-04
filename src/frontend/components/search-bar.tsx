"use client";

import { Input } from "@/components/ui/input";

interface SearchBarProps {
  value: string;
  onChange: (value: string) => void;
}

export function SearchBar({ value, onChange }: SearchBarProps) {
  return (
    <Input
      type="search"
      placeholder="Search articles..."
      aria-label="Search articles"
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="w-full max-w-sm"
    />
  );
}
