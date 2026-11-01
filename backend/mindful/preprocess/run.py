"""Run preprocessing for one participant and preset; CLI and cached entry point.

CLI: python -m mindful.preprocess.run <dataset_root> <T11|T5> <upstream|paper> [<out_dir>]

With an output directory, writes `<participant>_<preset>_<config digest>.json`
(diagnostics, including the dataset fingerprint) and `.npz` (derived arrays).
"""

import json
import sys
import time
from pathlib import Path
from typing import Any

from mindful.io.discovery import discover_participant
from mindful.io.inventory import fingerprint
from mindful.preprocess.config import PRESETS, PreprocessConfig
from mindful.preprocess.pipeline import diagnostics, prepare_participant, save_prepared


def output_stem(out_dir: Path, participant_id: str, config: PreprocessConfig) -> Path:
    """Cache files are keyed by participant and config digest, not by preset name."""
    return out_dir / f"{participant_id}_{config.digest()}"


def run_and_save(
    root: Path,
    participant_id: str,
    config: PreprocessConfig,
    out_dir: Path | None,
    label: str = "custom",
) -> dict[str, Any]:
    """Prepare one participant; optionally persist diagnostics and arrays."""
    t0 = time.perf_counter()
    prep = prepare_participant(discover_participant(root, participant_id), config)
    diag: dict[str, Any] = {
        "preset": label,
        "dataset_fingerprint": fingerprint(root),
        **diagnostics(prep),
        "elapsed_s": round(time.perf_counter() - t0, 1),
    }
    if out_dir is not None:
        stem = output_stem(out_dir, participant_id, config)
        save_prepared(prep, stem.with_suffix(".npz"))
        stem.with_suffix(".json").write_text(json.dumps(diag, indent=2), encoding="utf-8")
    return diag


def _print_summary(diag: dict[str, Any]) -> None:
    ref, pca, win, z = diag["reference"], diag["pca"], diag["windows"], diag["zscore"]
    dim = diag["config"]["pca_dim"]
    print(
        f"{diag['participant']} [{diag['preset']}] {diag['n_features']} features, "
        f"{diag['n_blocks']} blocks, {diag['n_selected_bins']} selected bins "
        f"({diag['elapsed_s']} s)"
    )
    print(
        f"  windows: {win['n_windows']} (step {win['step_bins']}, lastn {win['lastn']}), "
        f"{win['n_windows_crossing_blocks']} cross a block end, "
        f"{win['n_windows_crossing_sessions']} cross a session end, "
        f"{win['n_session_end_windows']} set to NaN later"
    )
    print(
        f"  reference: sessions {ref['sessions']} (days {ref['days']}), "
        f"{ref['candidate_bins']} candidate bins -> {ref['bins']} with AE < {ref['ae_max_deg']} "
        f"({ref['fraction_kept']:.1%}); {ref['candidate_ae_nan']} candidates had NaN AE"
    )
    top = ", ".join(f"{v:.2f}" for v in pca["explained_pct_top10"][:5])
    print(f"  PCA: top-{dim} explain {pca['cumulative_pct_at_dim']:.2f}% (first: {top})")
    print(
        f"  z-score: first bin exactly 0 in {z['blocks_first_bin_zero']}/{diag['n_blocks']} "
        f"blocks; floored std in {z['floored_std_fraction']:.4%} of values"
    )
    for s in diag["sessions"]:
        print(
            f"    S{s['session_index']:<2} day {s['day']}: {s['n_bins']} bins, "
            f"{s['n_windows']} windows, median AE {s['ae_median_deg']:.1f}"
        )


def main(argv: list[str]) -> int:
    if len(argv) < 3 or argv[2] not in PRESETS:
        print(__doc__)
        return 2
    out_dir = Path(argv[3]) if len(argv) > 3 else None
    _print_summary(run_and_save(Path(argv[0]), argv[1], PRESETS[argv[2]], out_dir, argv[2]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
