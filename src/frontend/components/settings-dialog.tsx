"use client";

import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";

export interface ApiKeyFeedback {
  status: "missing" | "invalid" | "accepted";
  message: string;
}

interface SettingsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  apiKey: string;
  onUpdateKey: (key: string) => void;
  onClearKey: () => void;
  feedback?: ApiKeyFeedback | null;
}

function maskKey(key: string): string {
  if (key.length <= 8) return "••••••••";
  return key.slice(0, 4) + "••••••••" + key.slice(-4);
}

export function SettingsDialog({
  open,
  onOpenChange,
  apiKey,
  onUpdateKey,
  onClearKey,
  feedback = null,
}: SettingsDialogProps) {
  const [newKey, setNewKey] = useState("");
  const [localMessage, setLocalMessage] = useState<{
    text: string;
    tone: "default" | "destructive";
  } | null>(null);
  const hasApiKey = apiKey.trim().length > 0;

  const handleUpdate = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmedKey = newKey.trim();
    if (trimmedKey) {
      onUpdateKey(trimmedKey);
      setNewKey("");
      setLocalMessage({
        text: hasApiKey
          ? "Saved your updated key in this browser. Refresh headlines to validate it."
          : "Saved your key in this browser. Refresh headlines to validate it.",
        tone: "default",
      });
    }
  };

  const handleRemove = () => {
    onClearKey();
    setNewKey("");
    setLocalMessage({
      text: "Removed the saved key. Cached articles still remain available.",
      tone: "default",
    });
  };

  const statusMessage = localMessage ?? (feedback
    ? {
        text: feedback.message,
        tone: feedback.status === "invalid" ? "destructive" : "default",
      }
    : null);

  const handleOpenChange = (nextOpen: boolean) => {
    if (!nextOpen) {
      setNewKey("");
      setLocalMessage(null);
    }
    onOpenChange(nextOpen);
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Settings</DialogTitle>
          <DialogDescription>
            Manage the NewsAPI key used when you refresh headlines.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {statusMessage && (
            <div
              aria-live="polite"
              className={cn(
                "rounded-md border px-3 py-2 text-sm",
                statusMessage.tone === "destructive"
                  ? "border-destructive/30 bg-destructive/10 text-destructive"
                  : "border-border bg-muted/40 text-foreground"
              )}
            >
              {statusMessage.text}
            </div>
          )}

          <div className="space-y-2">
            <p className="text-sm font-medium">Saved NewsAPI key</p>
            {hasApiKey ? (
              <>
                <p className="font-mono text-sm text-muted-foreground">
                  {maskKey(apiKey)}
                </p>
                <p className="text-xs text-muted-foreground">
                  Stored only in this browser and sent to the backend when you
                  choose refresh.
                </p>
              </>
            ) : (
              <>
                <p className="text-sm text-muted-foreground">
                  No NewsAPI key is saved yet.
                </p>
                <p className="text-xs text-muted-foreground">
                  Add one here or get a free key from{" "}
                  <a
                    href="https://newsapi.org/register"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="underline hover:text-foreground"
                  >
                    newsapi.org/register
                  </a>
                  .
                </p>
              </>
            )}
          </div>

          <form onSubmit={handleUpdate} className="space-y-2">
            <label htmlFor="new-api-key" className="text-sm font-medium">
              {hasApiKey ? "Update API Key" : "Add API Key"}
            </label>
            <div className="flex gap-2">
              <Input
                id="new-api-key"
                type="password"
                autoComplete="off"
                spellCheck={false}
                placeholder="Paste your NewsAPI key"
                value={newKey}
                onChange={(e) => setNewKey(e.target.value)}
              />
              <Button type="submit" disabled={!newKey.trim()}>
                {hasApiKey ? "Save" : "Add"}
              </Button>
            </div>
          </form>

          <div className="flex justify-between pt-2">
            {hasApiKey ? (
              <Button variant="destructive" size="sm" onClick={handleRemove}>
                Remove Key
              </Button>
            ) : (
              <div />
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleOpenChange(false)}
            >
              Close
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
