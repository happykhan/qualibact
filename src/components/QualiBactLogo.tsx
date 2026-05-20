/**
 * QualiBact logo: a metric distribution (bell curve) with two
 * threshold markers — the literal visualization at the heart of
 * every species page (a histogram with published lower/upper
 * QC bounds). Same style conventions as the rest of the
 * GenomicX fleet (24x24, stroke="var(--gx-accent)", strokeWidth=2).
 */
export default function QualiBactLogo({
  size = 26,
  className,
  ariaLabel,
}: {
  size?: number;
  className?: string;
  ariaLabel?: string;
}) {
  return (
    <svg
      className={className}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="var(--gx-accent)"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      role={ariaLabel ? 'img' : undefined}
      aria-label={ariaLabel}
      aria-hidden={ariaLabel ? undefined : true}
    >
      {/* Bell curve spanning the two threshold markers */}
      <path d="M6 19 C 8 19, 8 5, 12 5 C 16 5, 16 19, 18 19" />
      {/* Lower threshold marker */}
      <circle cx="6" cy="19" r="2" fill="var(--gx-accent)" />
      {/* Upper threshold marker */}
      <circle cx="18" cy="19" r="2" fill="var(--gx-accent)" />
    </svg>
  );
}
