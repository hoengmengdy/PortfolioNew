interface LogoProps {
  className?: string;
}

/** The HM mark, drawn as strokes so it stays crisp and needs no font. Decorative. */
export function LogoMark({ className = 'size-9' }: LogoProps) {
  return (
    <svg viewBox="0 0 48 48" fill="none" aria-hidden="true" className={className}>
      <defs>
        <linearGradient id="hm-gold" x1="0" y1="0" x2="48" y2="48" gradientUnits="userSpaceOnUse">
          <stop stopColor="#F5D76E" />
          <stop offset="1" stopColor="#B8922A" />
        </linearGradient>
      </defs>
      <rect x="1" y="1" width="46" height="46" rx="12" fill="#0B0B0B" stroke="url(#hm-gold)" />
      <path
        d="M11 15v18M21 15v18M11 24h10M27 33V15l5.5 11L38 15v18"
        stroke="url(#hm-gold)"
        strokeWidth="2.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
