/**
 * Two offset Gaussian contours: the reference day (bone) and the current window (signal).
 * The gap between them is what MINDFUL measures.
 */
export function LogoMark({ size = 28 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden focusable="false">
      <ellipse
        cx="13"
        cy="18"
        rx="7"
        ry="10.5"
        transform="rotate(-35 13 18)"
        fill="none"
        className="stroke-bone"
        strokeWidth="1.8"
      />
      <ellipse
        cx="19.5"
        cy="13.5"
        rx="7"
        ry="10.5"
        transform="rotate(-35 19.5 13.5)"
        fill="none"
        className="stroke-signal"
        strokeWidth="1.8"
      />
    </svg>
  );
}
