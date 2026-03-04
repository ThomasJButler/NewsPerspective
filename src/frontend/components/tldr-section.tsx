"use client";

interface TldrSectionProps {
  tldr: string;
}

export function TldrSection({ tldr }: TldrSectionProps) {
  return (
    <div className="bg-muted/50 rounded-lg px-4 py-3 border-l-4 border-primary/30">
      <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
        TLDR
      </span>
      <p className="mt-1 text-sm leading-relaxed">{tldr}</p>
    </div>
  );
}
