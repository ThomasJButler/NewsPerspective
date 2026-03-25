"use client";

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Separator } from "@/components/ui/separator";

interface AboutModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function AboutModal({ open, onOpenChange }: AboutModalProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="text-xl">NewsPerspective</DialogTitle>
          <DialogDescription>See the news. Not the spin.</DialogDescription>
        </DialogHeader>

        <div className="space-y-4 text-sm text-muted-foreground">
          <p>
            NewsPerspective uses AI to rewrite sensationalised headlines, provide
            TLDR summaries, and analyse sentiment. Stay informed without the
            fear-mongering, exaggeration, and ad clutter.
          </p>

          <Separator />

          <div className="space-y-2">
            <p className="font-medium text-foreground">How it works</p>
            <ul className="list-disc pl-5 space-y-1">
              <li>Fetches headlines from NewsAPI (US &amp; UK)</li>
              <li>AI analyses each article for sentiment and bias</li>
              <li>Sensationalised headlines are rewritten to be factual</li>
              <li>Good News filter excludes negativity-heavy categories</li>
            </ul>
          </div>

          <Separator />

          <div className="flex flex-col gap-2">
            <a
              href="https://github.com/ThomasJButler/NewsPerspective"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary hover:underline"
            >
              GitHub Repository
            </a>
            <a
              href="https://buymeacoffee.com/ojrwoqkgmv"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary hover:underline"
            >
              Buy Me a Coffee
            </a>
          </div>

          <Separator />

          <p className="text-xs">
            v3.0.0 &middot; Built by Tom Butler &middot; AGPLv3
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
}
