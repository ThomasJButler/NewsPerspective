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
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Settings</DialogTitle>
          <DialogDescription>
            Manage your NewsAPI key for fetching articles.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
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
      </DialogContent>
    </Dialog>
  );
}
