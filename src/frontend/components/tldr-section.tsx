"use client";

interface TldrSectionProps {
  tldr: string;
}

export function TldrSection({ tldr }: TldrSectionProps) {
  return (
    <div className="bg-muted/50 rounded-lg px-6 py-5 border-l-4 border-[color:var(--brand)] space-y-3">
      <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
        TLDR
      </span>
      <p className="text-sm leading-relaxed">{tldr}</p>
    </div>
  );
}
