/** Number formatting for tables. Missing values render as an em dash, never as 0. */

const DASH = "—";

export function int(value: number | null | undefined): string {
  return value == null ? DASH : value.toLocaleString("en-US");
}

export function fixed(value: number | null | undefined, digits = 1): string {
  return value == null ? DASH : value.toFixed(digits);
}

export function pct(fraction: number | null | undefined, digits = 1): string {
  return fraction == null ? DASH : `${(fraction * 100).toFixed(digits)}%`;
}

export function deg(value: number | null | undefined, digits = 1): string {
  return value == null ? DASH : `${value.toFixed(digits)}°`;
}

export function bytes(n: number): string {
  return n >= 1e6 ? `${(n / 1e6).toFixed(1)} MB` : `${(n / 1e3).toFixed(1)} kB`;
}

export function median(values: number[]): number | null {
  if (values.length === 0) return null;
  const s = [...values].sort((a, b) => a - b);
  const m = Math.floor(s.length / 2);
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
}
