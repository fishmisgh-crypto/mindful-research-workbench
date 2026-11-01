import type { Check } from "@/lib/api";

import { CheckMark } from "./StatusMark";

/** Validation checks as a hairline-ruled list: status, id, message. */
export function CheckList({ checks }: { checks: readonly Check[] }) {
  return (
    <ul className="border-rule border-t text-sm">
      {checks.map((check) => (
        <li
          key={check.id}
          className="border-rule grid grid-cols-[4.5rem_1fr] gap-x-4 border-b py-2 sm:grid-cols-[4.5rem_11rem_1fr]"
        >
          <span className="font-mono text-[12px]">
            <CheckMark status={check.status} />
          </span>
          <span className="text-ink-3 hidden font-mono text-[12px] sm:block">{check.id}</span>
          <span className="min-w-0 break-words">{check.message}</span>
        </li>
      ))}
    </ul>
  );
}
