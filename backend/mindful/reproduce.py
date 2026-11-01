"""Phase 5: run the reproduction matrix and compare with the published values.

Rules (REPRODUCTION_PLAN §3): run `upstream` first; change one parameter at a
time from `upstream`; report every run as computed. Published values are read
from `data/published_targets.json` for comparison only. Nothing here tunes,
filters or selects runs to approach them.

CLI: python -m mindful.reproduce <dataset_root> <processed_dir>
"""

import hashlib
import json
import sys
import time
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from mindful.ae_binned import PAPER_N_BINS, UPSTREAM_N_BINS, ae_binned_kld
from mindful.analysis import ANALYSIS_PRESETS, AnalysisConfig
from mindful.io.inventory import fingerprint
from mindful.preprocess.config import PRESETS
from mindful.runs import ensure_analysis, ensure_prepared

TARGETS_FILE = Path(__file__).parent / "data" / "published_targets.json"
UPSTREAM_COMMIT = "1809e132549f3c4b03327e3a14c748927d765e6e"
CORRELATION_METHOD = (
    "Pearson and Spearman over pairwise-complete windows "
    "(MATLAB corr, 'rows','complete'); no smoothing"
)

UPSTREAM = ANALYSIS_PRESETS["upstream"]
PAPER = ANALYSIS_PRESETS["paper"]
ABLATIONS: dict[str, tuple[AnalysisConfig, str]] = {
    "covariance": (
        AnalysisConfig("upstream + sample covariance", PRESETS["upstream"], "sample_covariance"),
        "D1: centred sample covariance instead of X'X/n",
    ),
    "step": (
        AnalysisConfig("upstream + 1 s step", PRESETS["paper"], "uncentered_second_moment"),
        "D2: windows every 50 bins (1 s) instead of 500 (10 s)",
    ),
    "excluded_trials": (
        AnalysisConfig(
            "upstream + excluded trials kept",
            replace(PRESETS["upstream"], include_excluded_trials=True),
            "uncentered_second_moment",
        ),
        "D3: outlier trials (excludeTrials) kept",
    ),
}
FIG1B_PREPROCESS = replace(PRESETS["upstream"], reference_scope="all")


@dataclass(frozen=True)
class RunSpec:
    id: str
    group: str  # primary | secondary | ablation
    participant: str
    feature_set: str
    config: AnalysisConfig
    varies: str  # what differs from the upstream preset


def run_specs() -> list[RunSpec]:
    specs: list[RunSpec] = []
    for p in ("T11", "T5"):
        for fs in ("pca5", "extended9"):
            specs.append(
                RunSpec(f"{p}-{fs}-upstream", "primary", p, fs, UPSTREAM, "none (upstream preset)")
            )
            specs.append(
                RunSpec(f"{p}-{fs}-paper", "primary", p, fs, PAPER, "D1 + D2 (paper preset)")
            )
        for fs in ("velocity2", "velocity4"):
            specs.append(
                RunSpec(
                    f"{p}-{fs}-upstream", "secondary", p, fs, UPSTREAM, "none (upstream preset)"
                )
            )
        for name, (config, varies) in ABLATIONS.items():
            if name == "excluded_trials" and p == "T5":
                continue  # T5 has no excluded trials: identical to upstream
            for fs in ("pca5", "extended9", "velocity2", "velocity4"):
                specs.append(RunSpec(f"{p}-{fs}-{name}", "ablation", p, fs, config, varies))
    return specs


def load_targets() -> dict[str, Any]:
    data: dict[str, Any] = json.loads(TARGETS_FILE.read_text(encoding="utf-8"))
    return data


def _target(targets: dict[str, Any], participant: str, feature_set: str) -> dict[str, Any] | None:
    for t in targets["correlations"]:
        if t["participant"] == participant and t["feature_set"] == feature_set:
            return dict(t)
    return None


def _delta(ours: float | None, published: float | None) -> float | None:
    if ours is None or published is None:
        return None
    return round(ours - published, 4)


def _verdict(deltas: list[float | None], tolerance: float) -> str:
    known = [d for d in deltas if d is not None]
    if not known:
        return "no published value"
    return "within tolerance" if all(abs(d) <= tolerance for d in known) else "differs"


def _row(spec: RunSpec, summary: dict[str, Any], targets: dict[str, Any]) -> dict[str, Any]:
    corr = summary["correlation"]
    target = _target(targets, spec.participant, spec.feature_set)
    dr = _delta(corr["pearson_r"], target["pearson"] if target else None)
    drho = _delta(corr["spearman_rho"], target["spearman"] if target else None)
    return {
        "id": spec.id,
        "group": spec.group,
        "participant": spec.participant,
        "feature_set": spec.feature_set,
        "preset": spec.config.preset,
        "varies": spec.varies,
        "config_digest": spec.config.digest(),
        "covariance_estimator": spec.config.covariance_estimator,
        "step_bins": spec.config.preprocess.step_bins,
        "n_windows": summary["n_windows"],
        "n_used": corr["n"],
        "pearson_r": corr["pearson_r"],
        "pearson_p": corr["pearson_p"],
        "spearman_rho": corr["spearman_rho"],
        "spearman_p": corr["spearman_p"],
        "published": target,
        "delta_r": dr,
        "delta_rho": drho,
        "verdict": _verdict([dr, drho], targets["match_tolerance"]),
        "kld_min": summary["kld_min"],
        "kld_max": summary["kld_max"],
        "n_reference_bins": summary["n_reference_bins"],
    }


def _ae_binned_rows(root: Path, processed: Path, targets: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for p in ("T11", "T5"):
        prep = ensure_prepared(
            root, processed, p, FIG1B_PREPROCESS, "fig1b (all-session AE<4 reference)"
        )
        target = next((t for t in targets["ae_binned"] if t["participant"] == p), None)
        for n_bins, label in (
            (UPSTREAM_N_BINS, "code loop (44 bins)"),
            (PAPER_N_BINS, "paper text (45 bins)"),
        ):
            res = ae_binned_kld(prep, n_bins, "uncentered_second_moment")
            dr = _delta(_round(res.correlation.pearson_r), target["pearson"] if target else None)
            rows.append(
                {
                    "id": f"{p}-fig1b-{n_bins}",
                    "participant": p,
                    "n_bins": n_bins,
                    "variant": label,
                    "n_reference_bins": int(prep.reference_bins.size),
                    "pearson_r": _round(res.correlation.pearson_r),
                    "pearson_p": res.correlation.pearson_p,
                    "n_used": res.correlation.n,
                    "published": target,
                    "delta_r": dr,
                    "verdict": _verdict([dr], targets["match_tolerance"]),
                    "bins": {
                        "lower_deg": res.lower_deg.tolist(),
                        "mean_ae": [_round(v, 4) for v in res.mean_ae],
                        "kld": [_round(v) for v in res.kld],
                        "n": res.n_bins_each.tolist(),
                        "reason": res.reasons,
                    },
                }
            )
    return rows


def _round(x: float, digits: int = 6) -> float | None:
    return None if x != x else round(float(x), digits)  # NaN check without numpy


def specs_digest() -> str:
    payload = [asdict(s) | {"config": s.config.as_dict()} for s in run_specs()]
    text = json.dumps(
        [payload, FIG1B_PREPROCESS.as_dict(), load_targets()], sort_keys=True, default=str
    )
    return hashlib.sha256(text.encode()).hexdigest()[:12]


def build_report(root: Path, processed: Path) -> dict[str, Any]:
    """Run (or reuse) every analysis in the matrix and assemble the comparison."""
    targets = load_targets()
    rows = []
    for spec in run_specs():
        result = ensure_analysis(root, processed, spec.participant, spec.config)
        rows.append(_row(spec, result["feature_sets"][spec.feature_set]["summary"], targets))
    return {
        "generated_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "dataset_fingerprint": fingerprint(root),
        "specs_digest": specs_digest(),
        "upstream_commit": UPSTREAM_COMMIT,
        "source": targets["source"],
        "match_tolerance": targets["match_tolerance"],
        "kld_range_approx": {
            k: v for k, v in targets["kld_range_approx"].items() if not k.startswith("_")
        },
        "correlation_method": CORRELATION_METHOD,
        "rows": rows,
        "ae_binned": _ae_binned_rows(root, processed, targets),
    }


def ensure_report(root: Path, processed: Path) -> dict[str, Any]:
    path = processed / "report" / f"reproduction_{specs_digest()}.json"
    try:
        cached: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        if cached.get("dataset_fingerprint") == fingerprint(root):
            return cached
    except (OSError, ValueError):
        pass
    report = build_report(root, processed)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def _fmt(v: float | None, digits: int = 3) -> str:
    return "—" if v is None else f"{v:.{digits}f}"


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to cp1252 (no Δ, ρ)
    t0 = time.perf_counter()
    report = ensure_report(Path(argv[0]), Path(argv[1]))
    elapsed = time.perf_counter() - t0
    print(f"Reproduction report ({elapsed:.0f} s), tolerance ±{report['match_tolerance']}")
    head = ("run", "n", "r", "pub r", "Δr", "ρ", "pub ρ", "Δρ")
    print(f"{head[0]:<30} " + " ".join(f"{h:>7}" for h in head[1:]) + "  verdict")
    for r in report["rows"]:
        pub = r["published"] or {}
        cells = (
            r["pearson_r"],
            pub.get("pearson"),
            r["delta_r"],
            r["spearman_rho"],
            pub.get("spearman"),
            r["delta_rho"],
        )
        line = " ".join(f"{_fmt(c):>7}" for c in cells)
        print(f"{r['id']:<30} {r['n_used']:>7} {line}  {r['verdict']}")
    for r in report["ae_binned"]:
        pub = r["published"] or {}
        line = " ".join(f"{_fmt(c):>7}" for c in (r["pearson_r"], pub.get("pearson"), r["delta_r"]))
        print(f"{r['id']:<30} {r['n_used']:>7} {line}  {r['variant']}; {r['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
