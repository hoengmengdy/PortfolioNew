/** The site's single loading indicator: a thin gold ring. */
export function Spinner({ label, className = 'size-11' }: { label: string; className?: string }) {
  return (
    <span role="status" className="inline-flex">
      <span
        aria-hidden="true"
        className={`animate-spin rounded-full border border-gold/25 border-t-gold ${className}`}
      />
      <span className="sr-only">{label}</span>
    </span>
  );
}
