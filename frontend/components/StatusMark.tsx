import type { CheckStatus } from "@/lib/api";

type Tone = "ok" | "pending" | "warn" | "fault";

const TONE_CLASS: Record<Tone, string> = {
  ok: "bg-ink",
  pending: "border border-ink-3 bg-transparent",
  warn: "border border-accent bg-transparent",
  fault: "bg-accent",
};

const CHECK_TONE: Record<CheckStatus, Tone> = {
  pass: "ok",
  info: "pending",
  warn: "warn",
  fail: "fault",
};

/** Small square status marker with a text label; colour is never the only signal. */
export function StatusMark({ tone, children }: { tone: Tone; children: string }) {
  return (
    <span className="inline-flex items-center gap-2">
      <span aria-hidden className={`inline-block size-2 shrink-0 ${TONE_CLASS[tone]}`} />
      <span>{children}</span>
    </span>
  );
}

export function CheckMark({ status }: { status: CheckStatus }) {
  return <StatusMark tone={CHECK_TONE[status]}>{status}</StatusMark>;
}
