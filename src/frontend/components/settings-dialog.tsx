"use client";

import { useCallback, useEffect, useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";
import { fetchGuardrails, updateGuardrails } from "@/lib/api";

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
  onGuardrailsUpdated?: () => Promise<void> | void;
  feedback?: ApiKeyFeedback | null;
}

function maskKey(key: string): string {
  if (key.length <= 8) return "••••••••";
  return key.slice(0, 4) + "••••••••" + key.slice(-4);
}

interface BlockedTopicsSectionProps {
  onGuardrailsUpdated?: () => Promise<void> | void;
}

function BlockedTopicsSection({
  onGuardrailsUpdated,
}: BlockedTopicsSectionProps) {
  const [keywords, setKeywords] = useState<string[]>([]);
  const [newKeyword, setNewKeyword] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  const loadKeywords = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      setNotice(null);
      const data = await fetchGuardrails();
      setKeywords(data.keywords);
    } catch {
      setError("Failed to load blocked topics.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadKeywords();
  }, [loadKeywords]);

  const saveKeywords = async (updated: string[]) => {
    try {
      setSaving(true);
      setError(null);
      setNotice(null);
      const data = await updateGuardrails(updated);
      setKeywords(data.keywords);

      if (onGuardrailsUpdated) {
        try {
          await onGuardrailsUpdated();
        } catch {
          setNotice(
            "Blocked topics were saved, but the feed did not refresh. Close Settings or refresh the page to see the latest filters."
          );
        }
      }
    } catch {
      setError("Failed to save blocked topics.");
    } finally {
      setSaving(false);
    }
  };

  const handleAdd = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = newKeyword.trim().toLowerCase();
    if (!trimmed || keywords.includes(trimmed)) {
      setNewKeyword("");
      return;
    }
    const updated = [...keywords, trimmed];
    setNewKeyword("");
    saveKeywords(updated);
  };

  const handleRemove = (keyword: string) => {
    const updated = keywords.filter((k) => k !== keyword);
    saveKeywords(updated);
  };

  return (
    <div className="space-y-2">
      <p className="text-sm font-medium">Blocked topics</p>
      <p className="text-xs text-muted-foreground">
        Articles matching these keywords are hidden from the feed and
        comparison view. Up to 50 keywords.
      </p>

      {error && (
        <div
          aria-live="polite"
          className="rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive"
        >
          {error}
        </div>
      )}

      {notice && (
        <div
          aria-live="polite"
          className="rounded-md border border-border bg-muted/40 px-3 py-2 text-sm text-foreground"
        >
          {notice}
        </div>
      )}

      {loading ? (
        <p className="text-sm text-muted-foreground">Loading...</p>
      ) : (
        <>
          {keywords.length > 0 && (
            <div className="flex flex-wrap gap-1.5" aria-label="Blocked keywords">
              {keywords.map((kw) => (
                <Badge key={kw} variant="secondary" className="gap-1 pr-1">
                  {kw}
                  <button
                    type="button"
                    aria-label={`Remove ${kw}`}
                    disabled={saving}
                    onClick={() => handleRemove(kw)}
                    className="ml-0.5 rounded-full p-0.5 hover:bg-muted-foreground/20"
                  >
                    <svg
                      width="12"
                      height="12"
                      viewBox="0 0 12 12"
                      fill="none"
                      aria-hidden="true"
                    >
                      <path
                        d="M3 3l6 6M9 3l-6 6"
                        stroke="currentColor"
                        strokeWidth="1.5"
                        strokeLinecap="round"
                      />
                    </svg>
                  </button>
                </Badge>
              ))}
            </div>
          )}

          <form onSubmit={handleAdd} className="flex gap-2">
            <Input
              type="text"
              placeholder="Add a keyword to block"
              aria-label="New blocked keyword"
              value={newKeyword}
              onChange={(e) => setNewKeyword(e.target.value)}
              maxLength={100}
            />
            <Button
              type="submit"
              size="sm"
              disabled={!newKeyword.trim() || saving}
            >
              Add
            </Button>
          </form>
        </>
      )}
    </div>
  );
}

export function SettingsDialog({
  open,
  onOpenChange,
  apiKey,
  onUpdateKey,
  onClearKey,
  onGuardrailsUpdated,
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
            Manage your NewsAPI key and content preferences.
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

          <Separator />

          {open && <BlockedTopicsSection onGuardrailsUpdated={onGuardrailsUpdated} />}

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
