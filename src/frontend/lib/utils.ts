import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

const MINUTE = 60;
const HOUR = 3600;
const DAY = 86400;

export function formatDate(dateString: string | null): string {
  if (!dateString) return "";
  const date = new Date(dateString);
  const now = new Date();
  const diffSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (diffSeconds < MINUTE) return "just now";
  if (diffSeconds < HOUR) {
    const m = Math.floor(diffSeconds / MINUTE);
    return `${m} minute${m !== 1 ? "s" : ""} ago`;
  }
  if (diffSeconds < DAY) {
    const h = Math.floor(diffSeconds / HOUR);
    return `${h} hour${h !== 1 ? "s" : ""} ago`;
  }
  if (diffSeconds < DAY * 7) {
    const d = Math.floor(diffSeconds / DAY);
    return `${d} day${d !== 1 ? "s" : ""} ago`;
  }
  return date.toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength).trimEnd() + "…";
}
