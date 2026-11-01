"""CLI: python -m mindful.cli analyse <dataset_root> <processed_dir> <T11|T5> <upstream|paper>

Prepares (or reuses) the participant's features, computes KLD and median AE for
every window and feature set, writes the result, and prints a summary.
"""

import sys
import time
from pathlib import Path

from mindful.analysis import ANALYSIS_PRESETS
from mindful.runs import analysis_path, ensure_analysis


def main(argv: list[str]) -> int:
    if len(argv) != 5 or argv[0] != "analyse" or argv[4] not in ANALYSIS_PRESETS:
        print(__doc__)
        return 2
    root, processed, participant, preset = Path(argv[1]), Path(argv[2]), argv[3], argv[4]
    t0 = time.perf_counter()
    config = ANALYSIS_PRESETS[preset]
    result = ensure_analysis(root, processed, participant, config)
    cfg = result["config"]
    print(
        f"{participant} [{preset}] covariance={cfg['covariance_estimator']} "
        f"step={result['step_bins']} window={result['window_bins']} "
        f"({time.perf_counter() - t0:.1f} s) -> {analysis_path(processed, participant, config)}"
    )
    for name, fs in result["feature_sets"].items():
        s = fs["summary"]
        print(
            f"  {name:<10} dim {s['dim']}: {s['n_valid']}/{s['n_windows']} valid windows, "
            f"reasons {s['reasons']}, KLD min/median/max "
            f"{s['kld_min']:.4g} / {s['kld_median']:.4g} / {s['kld_max']:.4g}, "
            f"negative {s['kld_negative']}, ref cond {s['reference_condition']}, "
            f"max window cond {s['window_condition_max']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
