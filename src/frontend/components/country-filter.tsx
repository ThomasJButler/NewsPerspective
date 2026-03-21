"use client";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface CountryFilterProps {
  value: string;
  onValueChange: (value: string) => void;
}

export function CountryFilter({ value, onValueChange }: CountryFilterProps) {
  return (
    <Select value={value} onValueChange={onValueChange}>
      <SelectTrigger className="w-[160px]" aria-label="Filter by country">
        <SelectValue placeholder="All Countries" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="all">All Countries</SelectItem>
        <SelectItem value="us">US</SelectItem>
        <SelectItem value="gb">UK</SelectItem>
      </SelectContent>
    </Select>
  );
}
