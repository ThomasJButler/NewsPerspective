interface BrandLogoProps {
  className?: string;
  size?: number;
}

/**
 * NewsPerspective brand mark — an "N" monogram inside a rounded square,
 * tinted with the --brand CSS variable so it tracks light/dark themes.
 *
 * Designed to stay legible from 16px (favicon) to 48px (header).
 */
export function BrandLogo({ className, size = 32 }: BrandLogoProps) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width={size}
      height={size}
      viewBox="0 0 32 32"
      role="img"
      aria-label="NewsPerspective logo"
      className={className}
    >
      <rect
        x="1"
        y="1"
        width="30"
        height="30"
        rx="7"
        fill="var(--brand)"
      />
      {/* Stylised "N": two vertical stems linked by a diagonal stroke. */}
      <path
        d="M8 9 H12 L20 19 V9 H24 V23 H20 L12 13 V23 H8 Z"
        fill="var(--brand-foreground)"
      />
    </svg>
  );
}
