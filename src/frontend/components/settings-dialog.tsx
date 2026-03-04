"use client";

import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

interface SettingsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  apiKey: string;
  onUpdateKey: (key: string) => void;
  onClearKey: () => void;
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
}: SettingsDialogProps) {
  const [newKey, setNewKey] = useState("");

  if (!open) return null;

  const handleUpdate = (e: React.FormEvent) => {
    e.preventDefault();
    if (newKey.trim()) {
      onUpdateKey(newKey.trim());
      setNewKey("");
      onOpenChange(false);
    }
  };

  const handleRemove = () => {
    onClearKey();
    onOpenChange(false);
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={(e) => {
        if (e.target === e.currentTarget) onOpenChange(false);
      }}
      onKeyDown={(e) => {
        if (e.key === "Escape") onOpenChange(false);
      }}
      role="dialog"
      aria-label="Settings"
      aria-modal="true"
    >
      <div className="bg-background rounded-lg border shadow-lg p-6 w-full max-w-md space-y-4">
        <h2 className="text-lg font-semibold">Settings</h2>

        <div className="space-y-2">
          <label className="text-sm font-medium">Current API Key</label>
          <p className="text-sm text-muted-foreground font-mono">
            {maskKey(apiKey)}
          </p>
        </div>

        <form onSubmit={handleUpdate} className="space-y-2">
          <label htmlFor="new-api-key" className="text-sm font-medium">
            Change API Key
          </label>
          <div className="flex gap-2">
            <Input
              id="new-api-key"
              type="text"
              placeholder="New API key"
              value={newKey}
              onChange={(e) => setNewKey(e.target.value)}
            />
            <Button type="submit" disabled={!newKey.trim()}>
              Update
            </Button>
          </div>
        </form>

        <div className="flex justify-between pt-2">
          <Button variant="destructive" size="sm" onClick={handleRemove}>
            Remove Key
          </Button>
          <Button variant="outline" size="sm" onClick={() => onOpenChange(false)}>
            Close
          </Button>
        </div>
      </div>
    </div>
  );
}
