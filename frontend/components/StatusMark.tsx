type Tone = "ok" | "pending" | "fault";

const TONE_CLASS: Record<Tone, string> = {
  ok: "bg-ink",
  pending: "border border-ink-3 bg-transparent",
  fault: "bg-accent",
};

/** Small square status marker with a text label; colour is never the only signal. */
export function StatusMark({ tone, children }: { tone: Tone; children: string }) {
  return (
    <span className="inline-flex items-center gap-2">
      <span aria-hidden className={`inline-block size-2 ${TONE_CLASS[tone]}`} />
      <span>{children}</span>
    </span>
  );
}
