"use client";

import { X } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";

export function Toaster() {
  const { toasts, dismiss } = useToast();

  if (toasts.length === 0) return null;

  return (
    <div
      className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 w-full max-w-sm"
      role="region"
      aria-label="Notifications"
    >
      {toasts.map((t) => (
        <div
          key={t.id}
          role="alert"
          className={cn(
            "rounded-lg border p-4 shadow-lg animate-in slide-in-from-bottom-2 fade-in-0",
            "bg-background text-foreground",
            t.variant === "destructive" &&
              "border-destructive bg-destructive text-white"
          )}
        >
          <div className="flex items-start justify-between gap-2">
            <div className="space-y-1">
              <p className="text-sm font-semibold">{t.title}</p>
              {t.description && (
                <p className="text-sm opacity-90">{t.description}</p>
              )}
            </div>
            <button
              onClick={() => dismiss(t.id)}
              className="shrink-0 rounded-sm opacity-70 hover:opacity-100"
              aria-label="Dismiss"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
