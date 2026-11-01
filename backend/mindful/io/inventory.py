"""Dataset inventory: every session and block with summary statistics and checks.

The inventory holds aggregates and metadata only, never raw neural matrices.
Documented counts come from the paper and the Dryad README; they are
compared, never enforced or used to adjust anything.

CLI: python -m mindful.io.inventory <dataset_root> [<output.json>]
"""

import hashlib
import json
import sys
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from mindful.io.block import LOAD_ERRORS, Block, load_block
from mindful.io.discovery import BlockRef, ParticipantRef, SessionRef, discover
from mindful.io.validation import Check, Status, validate_block, worst

SCHEMA_VERSION = 1
BIN_SECONDS = 0.02
ADDITIONAL_FOLDER = "T11(additional)"

# Documented in the paper / Dryad README. Compared against, never enforced.
DOCUMENTED: dict[str, dict[str, int]] = {
    "T11": {"sessions": 15, "blocks": 29, "trials": 1840, "excluded_trials": 34, "features": 384},
    "T5": {"sessions": 6, "trials": 1200, "excluded_trials": 0, "features": 192},
}


def _mat_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.mat") if p.is_file())


def fingerprint(root: Path) -> str:
    """Cheap change detector: relative path, size and mtime of every .mat file."""
    h = hashlib.sha256()
    for p in _mat_files(root):
        st = p.stat()
        h.update(f"{p.relative_to(root).as_posix()}|{st.st_size}|{st.st_mtime_ns}\n".encode())
    return h.hexdigest()


def content_digest(root: Path) -> tuple[str, int, int]:
    """SHA-256 over sorted 'relpath sha256' lines of every .mat file; plus file count and bytes."""
    lines: list[str] = []
    total = 0
    for p in _mat_files(root):
        file_hash = hashlib.sha256(p.read_bytes()).hexdigest()
        total += p.stat().st_size
        lines.append(f"{p.relative_to(root).as_posix()} {file_hash}")
    return hashlib.sha256("\n".join(lines).encode()).hexdigest(), len(lines), total


def _check_dict(c: Check) -> dict[str, str]:
    return asdict(c)


def _nan_stat(value: float) -> float | None:
    return None if not np.isfinite(value) else round(float(value), 6)


def block_summary(block: Block, checks: list[Check]) -> dict[str, Any]:
    kept = block.trial_mask()
    ae_kept = block.angle_error[kept]
    outlier_frac = (
        float(np.mean(block.avg_outliers > 0)) if block.avg_outliers is not None else float("nan")
    )
    return {
        "number": block.ref.number,
        "name": block.ref.name,
        "task_name": block.task_name,
        "n_bins": block.n_bins,
        "duration_s": round(block.n_bins * BIN_SECONDS, 2),
        "n_trials": block.n_trials,
        "n_excluded_trials": int(block.exclude_trials.sum()),
        "kept_trial_bins": int(kept.sum()),
        "feature_count": int(block.neural.shape[1]),
        "has_spike_power": block.spike_power is not None,
        "percent_correct": _nan_stat(block.percent_correct)
        if block.percent_correct is not None
        else None,
        "ae_median_kept_deg": _nan_stat(float(np.nanmedian(ae_kept)))
        if np.isfinite(ae_kept).any()
        else None,
        "ae_nan_fraction": _nan_stat(float(np.isnan(block.angle_error).mean())),
        "nctx_mean_rate": _nan_stat(float(block.nctx.mean())),
        "outlier_bin_fraction": _nan_stat(outlier_frac),
        "status": worst(checks),
        "checks": [_check_dict(c) for c in checks],
    }


def _failed_block(ref: BlockRef, error: str) -> dict[str, Any]:
    check = Check("load", "fail", error)
    return {
        "number": ref.number,
        "name": ref.name,
        "status": "fail",
        "checks": [_check_dict(check)],
    }


def _session_summary(session: SessionRef) -> dict[str, Any]:
    blocks: list[dict[str, Any]] = []
    for ref in session.blocks:
        try:
            block = load_block(ref)
        except LOAD_ERRORS as exc:
            blocks.append(_failed_block(ref, f"{type(exc).__name__}: {exc}"))
            continue
        blocks.append(block_summary(block, validate_block(block)))
    statuses: list[Status] = [b["status"] for b in blocks]
    return {
        "day": session.day,
        "index": session.index,
        "name": session.name,
        "n_blocks": len(blocks),
        "block_mtime_order_matches_numeric": session.block_mtime_order_matches_numeric,
        "status": worst([Check("", s, "") for s in statuses]),
        "blocks": blocks,
    }


def _compare(cid: str, label: str, observed: int, documented: int | None) -> Check:
    if documented is None:
        return Check(cid, "info", f"{label}: {observed} (no documented value)")
    if observed == documented:
        return Check(cid, "pass", f"{label}: {observed}, as documented")
    return Check(cid, "warn", f"{label}: {observed} observed, {documented} documented")


def _participant_summary(p: ParticipantRef) -> dict[str, Any]:
    sessions = [_session_summary(s) for s in p.sessions]
    loaded = [b for s in sessions for b in s["blocks"] if "n_bins" in b]
    n_blocks = sum(s["n_blocks"] for s in sessions)
    totals = {
        "n_sessions": len(sessions),
        "n_blocks": n_blocks,
        "n_trials": sum(b["n_trials"] for b in loaded),
        "n_excluded_trials": sum(b["n_excluded_trials"] for b in loaded),
        "n_bins": sum(b["n_bins"] for b in loaded),
        "kept_trial_bins": sum(b["kept_trial_bins"] for b in loaded),
    }
    doc = DOCUMENTED.get(p.id, {})
    features = sorted({b["feature_count"] for b in loaded})
    tasks = sorted({b["task_name"] for b in loaded})
    checks = [
        _compare("sessions", "Sessions", totals["n_sessions"], doc.get("sessions")),
        _compare("blocks", "Blocks", n_blocks, doc.get("blocks")),
        _compare("trials", "Trials", totals["n_trials"], doc.get("trials")),
        _compare(
            "excluded_trials",
            "Excluded trials",
            totals["n_excluded_trials"],
            doc.get("excluded_trials"),
        ),
        Check(
            "features",
            "pass" if features == [doc.get("features")] else "warn",
            f"Feature count per block: {', '.join(map(str, features))} "
            f"(documented {doc.get('features')}, D8)",
        ),
        Check(
            "load",
            "pass" if len(loaded) == n_blocks else "fail",
            f"{len(loaded)} of {n_blocks} blocks loaded",
        ),
        Check(
            "session_order",
            "pass" if p.dir_order_matches_chronological else "warn",
            "MATLAB dir (alphabetical) session order "
            + ("matches" if p.dir_order_matches_chronological else "differs from")
            + " chronological order (D5)",
        ),
        Check(
            "block_order",
            "info",
            f"File-modification-time block order matches block number in "
            f"{sum(s['block_mtime_order_matches_numeric'] for s in sessions)} of "
            f"{len(sessions)} sessions "
            "(D6; numeric order is used)",
        ),
        Check("task_names", "info", f"Task name(s): {', '.join(tasks)}"),
    ]
    if p.ignored_entries:
        checks.append(Check("ignored_entries", "info", f"Ignored: {', '.join(p.ignored_entries)}"))
    return {
        "id": p.id,
        **totals,
        "duration_min": round(totals["n_bins"] * BIN_SECONDS / 60, 2),
        "feature_counts": features,
        "task_names": tasks,
        "session_order": {
            "chronological": list(p.chronological_order),
            "matlab_dir": list(p.matlab_dir_order),
            "matches": p.dir_order_matches_chronological,
        },
        "status": worst(checks + [Check("", s["status"], "") for s in sessions]),
        "checks": [_check_dict(c) for c in checks],
        "sessions": sessions,
    }


def _additional(root: Path) -> list[str]:
    folder = root / ADDITIONAL_FOLDER
    if not folder.is_dir():
        return []
    return sorted(
        p.relative_to(root).as_posix() for p in folder.glob("*/day_*/Block_*") if p.is_dir()
    )


def build_inventory(root: Path) -> dict[str, Any]:
    """Load every block once and return the JSON-serialisable inventory."""
    digest, n_files, n_bytes = content_digest(root)
    participants = discover(root)
    return {
        "schema_version": SCHEMA_VERSION,
        "built_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "root": str(root),
        "fingerprint": fingerprint(root),
        "content_digest_sha256": digest,
        "n_mat_files": n_files,
        "mat_bytes": n_bytes,
        "documented": DOCUMENTED,
        "participants": [_participant_summary(p) for p in participants.values()],
        "out_of_scope_blocks": _additional(root),
    }


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    inventory = build_inventory(Path(argv[0]))
    text = json.dumps(inventory, indent=2)
    if len(argv) > 1:
        Path(argv[1]).parent.mkdir(parents=True, exist_ok=True)
        Path(argv[1]).write_text(text, encoding="utf-8")
    for p in inventory["participants"]:
        print(f"{p['id']}: {p['status']}")
        for c in p["checks"]:
            print(f"  [{c['status']:4s}] {c['message']}")
    print(f"content digest {inventory['content_digest_sha256']} ({inventory['n_mat_files']} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
