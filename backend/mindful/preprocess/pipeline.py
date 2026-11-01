"""Participant-level preprocessing: everything the KLD engine needs, nothing more.

Steps (RESEARCH_SPEC §3.1–3.7):
  1. per block, in chronological session order and block-number order:
     z-score the full block (§3.2), keep bins of non-excluded trials (§3.3),
     lag cursorVel on the full block, then subset (§3.7)
  2. window index over the concatenated selected bins (§3.4)
  3. reference bins = bins covered by the reference sessions' windows,
     minus the last lastn-1 windows, with angleError < 4 (§3.5)
  4. PCA fitted on reference bins only; every selected bin projected (§3.6)

Raw feature matrices are processed one block at a time and never concatenated:
only the projected scores (n_bins x pca_dim) are kept.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
import numpy.typing as npt

from mindful.io.block import Block, load_block
from mindful.io.discovery import BlockRef, ParticipantRef
from mindful.preprocess.config import REFERENCE_SESSIONS, PreprocessConfig
from mindful.preprocess.lag import lag_within_block
from mindful.preprocess.pca import PcaModel, fit_pca
from mindful.preprocess.windows import WindowIndex, build_windows
from mindful.preprocess.zscore import rolling_stats

FloatArray = npt.NDArray[np.float64]
IntArray = npt.NDArray[np.int64]

FEATURE_SETS: dict[str, str] = {
    "pca5": "top PCs (NF, Fig 1c, Configuration 1)",
    "extended9": "top PCs + cursorVel(t) + cursorVel(t-1) (NFXhatlag, Fig 2c, Configuration 2)",
    "velocity2": "cursorVel(t) (Xhat, Fig 2a)",
    "velocity4": "cursorVel(t) + cursorVel(t-1) (Xhatlag, Fig 2b)",
}


@dataclass(frozen=True)
class BlockPlan:
    position: int
    session_index: int  # 1-based chronological
    day: int
    number: int
    n_bins: int
    n_selected: int
    offset: int  # first position of this block's bins in the concatenation


_BLOCK_FIELDS = ("position", "session_index", "day", "number", "n_bins", "n_selected", "offset")


@dataclass
class ZscoreAudit:
    blocks_first_bin_zero: int = 0
    floored_std_values: int = 0
    total_values: int = 0
    max_abs_first_bin: float = 0.0


@dataclass
class PreparedParticipant:
    participant: str
    config: PreprocessConfig
    blocks: list[BlockPlan]
    windows: WindowIndex
    angle_error: FloatArray
    velocity: FloatArray
    velocity_lag: FloatArray
    pc_scores: FloatArray
    pca: PcaModel
    reference_sessions: tuple[int, ...]
    reference_bins: IntArray
    reference_candidate_bins: int
    reference_candidate_ae_nan: int
    n_features: int
    zscore_audit: ZscoreAudit = field(default_factory=ZscoreAudit)

    @property
    def n_bins(self) -> int:
        return int(self.angle_error.size)

    def features(self, name: str) -> FloatArray:
        if name == "pca5":
            return self.pc_scores
        if name == "extended9":
            return np.hstack([self.pc_scores, self.velocity, self.velocity_lag])
        if name == "velocity2":
            return self.velocity
        if name == "velocity4":
            return np.hstack([self.velocity, self.velocity_lag])
        raise KeyError(f"unknown feature set {name!r}; choose from {sorted(FEATURE_SETS)}")

    def session_of_bin(self) -> IntArray:
        return np.repeat(
            np.array([b.session_index for b in self.blocks], dtype=np.int64),
            [b.n_selected for b in self.blocks],
        )


def _ordered_blocks(participant: ParticipantRef) -> list[tuple[int, BlockRef]]:
    return [(s.index, ref) for s in participant.sessions for ref in s.blocks]


def _selected_zscore(block: Block, config: PreprocessConfig, audit: ZscoreAudit) -> FloatArray:
    """z-score the whole block, then keep selected bins (z-scoring sees non-trial bins too)."""
    x = block.neural
    mean, std = rolling_stats(x, config.zscore_window_bins)
    floored = std < config.zscore_std_floor
    audit.floored_std_values += int(floored.sum())
    audit.total_values += int(floored.size)
    std = np.where(floored, 1.0, std)
    z = (x - mean) / std
    first = float(np.max(np.abs(z[0])))
    audit.max_abs_first_bin = max(audit.max_abs_first_bin, first)
    audit.blocks_first_bin_zero += int(first == 0.0)
    selected: FloatArray = z[block.trial_mask(config.include_excluded_trials)]
    return selected


def prepare_participant(
    participant: ParticipantRef, config: PreprocessConfig
) -> PreparedParticipant:
    """Run steps 1–4 for one participant."""
    ordered = _ordered_blocks(participant)
    plans: list[BlockPlan] = []
    ae_parts: list[FloatArray] = []
    vel_parts: list[FloatArray] = []
    lag_parts: list[FloatArray] = []
    n_features = 0
    offset = 0

    # Pass 1: selection, behaviour and lag (cheap arrays only).
    for position, (session_index, ref) in enumerate(ordered):
        block = load_block(ref)
        mask = block.trial_mask(config.include_excluded_trials)
        n_features = block.neural.shape[1]
        ae_parts.append(block.angle_error[mask])
        vel_parts.append(block.cursor_vel[mask])
        lag_parts.append(lag_within_block(block.cursor_vel, config.velocity_lag_bins)[mask])
        n_sel = int(mask.sum())
        plans.append(
            BlockPlan(position, session_index, ref.day, ref.number, block.n_bins, n_sel, offset)
        )
        offset += n_sel

    angle_error = np.concatenate(ae_parts)
    windows = build_windows(
        np.array([p.n_selected for p in plans]),
        np.array([p.session_index for p in plans]),
        config.window_bins,
        config.step_bins,
    )

    # Reference bins: windows of the reference sessions, then AE < threshold.
    ref_sessions = REFERENCE_SESSIONS[participant.id]
    candidates = windows.bins_covered(windows.session_reference_windows(ref_sessions))
    ae_c = angle_error[candidates]
    reference_bins = candidates[np.nan_to_num(ae_c, nan=np.inf) < config.reference_ae_max_deg]

    # Pass 2: z-score; fit PCA on reference blocks, then project every block.
    audit = ZscoreAudit()
    offsets = np.array([p.offset for p in plans], dtype=np.int64)
    block_of_ref = np.searchsorted(offsets, reference_bins, side="right") - 1
    cached: dict[int, FloatArray] = {}
    ref_rows: list[FloatArray] = []
    for pos in np.unique(block_of_ref).tolist():
        cached[pos] = _selected_zscore(load_block(ordered[pos][1]), config, audit)
        local = reference_bins[block_of_ref == pos] - plans[pos].offset
        ref_rows.append(cached[pos][local])
    pca = fit_pca(np.vstack(ref_rows))
    del ref_rows

    scores = np.empty((windows.n_bins, config.pca_dim))
    for pos, (_, ref) in enumerate(ordered):
        z = cached.pop(pos) if pos in cached else _selected_zscore(load_block(ref), config, audit)
        p = plans[pos]
        scores[p.offset : p.offset + p.n_selected] = pca.transform(z, config.pca_dim)

    return PreparedParticipant(
        participant=participant.id,
        config=config,
        blocks=plans,
        windows=windows,
        angle_error=angle_error,
        velocity=np.concatenate(vel_parts),
        velocity_lag=np.concatenate(lag_parts),
        pc_scores=scores,
        pca=pca,
        reference_sessions=ref_sessions,
        reference_bins=reference_bins,
        reference_candidate_bins=int(candidates.size),
        reference_candidate_ae_nan=int(np.isnan(ae_c).sum()),
        n_features=n_features,
        zscore_audit=audit,
    )


def diagnostics(prep: PreparedParticipant) -> dict[str, Any]:
    """JSON-serialisable summary for inspection. Aggregates only."""
    w = prep.windows
    session_of_bin = prep.session_of_bin()
    block_end = np.array([b.offset + b.n_selected - 1 for b in prep.blocks], dtype=np.int64)
    ref_scores = prep.pc_scores[prep.reference_bins]
    sessions = sorted({b.session_index for b in prep.blocks})
    day_of_session = {b.session_index: b.day for b in prep.blocks}
    per_session = []
    for s in sessions:
        sel = session_of_bin == s
        per_session.append(
            {
                "session_index": s,
                "day": day_of_session[s],
                "n_bins": int(sel.sum()),
                "n_windows": int((w.session_of_window == s).sum()),
                "pc_mean": np.round(prep.pc_scores[sel].mean(axis=0), 4).tolist(),
                "pc_std": np.round(prep.pc_scores[sel].std(axis=0), 4).tolist(),
                "ae_median_deg": _round(float(np.nanmedian(prep.angle_error[sel]))),
            }
        )
    audit = prep.zscore_audit
    explained = prep.pca.explained_pct
    return {
        "participant": prep.participant,
        "config": prep.config.as_dict(),
        "config_digest": prep.config.digest(),
        "n_features": prep.n_features,
        "n_blocks": len(prep.blocks),
        "n_selected_bins": prep.n_bins,
        "blocks": [
            {
                "session_index": b.session_index,
                "day": b.day,
                "block": b.number,
                "n_bins": b.n_bins,
                "n_selected": b.n_selected,
                "n_windows": int(w.seg_per_block[b.position]),
            }
            for b in prep.blocks
        ],
        "windows": {
            "n_windows": w.n_windows,
            "window_bins": w.window_bins,
            "step_bins": w.step_bins,
            "lastn": w.lastn,
            "n_session_end_windows": int(w.session_end_windows().size),
            "n_windows_crossing_blocks": int(np.sum(w.stops > block_end[w.block_of_window])),
            "n_windows_crossing_sessions": int(
                np.sum(session_of_bin[w.stops] != w.session_of_window)
            ),
        },
        "reference": {
            "sessions": list(prep.reference_sessions),
            "days": [day_of_session[s] for s in prep.reference_sessions],
            "candidate_bins": prep.reference_candidate_bins,
            "candidate_ae_nan": prep.reference_candidate_ae_nan,
            "bins": int(prep.reference_bins.size),
            "ae_max_deg": prep.config.reference_ae_max_deg,
            "fraction_kept": _round(
                prep.reference_bins.size / max(prep.reference_candidate_bins, 1)
            ),
        },
        "pca": {
            "n_reference_bins": prep.pca.n_reference_bins,
            "explained_pct_top10": np.round(explained[:10], 4).tolist(),
            "cumulative_pct_at_dim": _round(float(explained[: prep.config.pca_dim].sum())),
            "explained_pct_sum": _round(float(explained.sum())),
            "reference_score_mean": np.round(ref_scores.mean(axis=0), 10).tolist(),
            "reference_score_std": np.round(ref_scores.std(axis=0, ddof=1), 4).tolist(),
        },
        "zscore": {
            "trailing_bins": prep.config.zscore_window_bins,
            "blocks_first_bin_zero": audit.blocks_first_bin_zero,
            "max_abs_first_bin": audit.max_abs_first_bin,
            "floored_std_fraction": _round(
                audit.floored_std_values / max(audit.total_values, 1), 8
            ),
        },
        "sessions": per_session,
        "feature_sets": FEATURE_SETS,
    }


def _round(x: float, digits: int = 6) -> float | None:
    return None if not np.isfinite(x) else round(float(x), digits)


def save_prepared(prep: PreparedParticipant, path: Path) -> None:
    """Persist everything the KLD engine needs (npz; derived data, never raw matrices)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    audit = prep.zscore_audit
    np.savez_compressed(
        path,
        participant=np.array(prep.participant),
        config=np.array(json.dumps(prep.config.as_dict())),
        blocks=np.array(
            [[getattr(b, f) for f in _BLOCK_FIELDS] for b in prep.blocks], dtype=np.int64
        ),
        angle_error=prep.angle_error,
        velocity=prep.velocity,
        velocity_lag=prep.velocity_lag,
        pc_scores=prep.pc_scores,
        reference_sessions=np.array(prep.reference_sessions, dtype=np.int64),
        reference_bins=prep.reference_bins,
        reference_candidate=np.array(
            [prep.reference_candidate_bins, prep.reference_candidate_ae_nan, prep.n_features]
        ),
        pca_mean=prep.pca.mean,
        pca_components=prep.pca.components[:, : prep.config.pca_dim],
        pca_explained=prep.pca.explained_pct,
        pca_n_reference=np.array(prep.pca.n_reference_bins),
        zscore_audit=np.array(
            [audit.blocks_first_bin_zero, audit.floored_std_values, audit.total_values]
        ),
        zscore_max_first=np.array(audit.max_abs_first_bin),
    )


def load_prepared(path: Path) -> PreparedParticipant:
    """Inverse of `save_prepared`. The window index is rebuilt deterministically."""
    with np.load(path, allow_pickle=False) as f:
        config = PreprocessConfig(**json.loads(str(f["config"])))
        blocks = [BlockPlan(*map(int, row)) for row in f["blocks"]]
        candidate, n_ref_nan, n_features = (int(v) for v in f["reference_candidate"])
        first_zero, floored, total = (int(v) for v in f["zscore_audit"])
        windows = build_windows(
            np.array([b.n_selected for b in blocks]),
            np.array([b.session_index for b in blocks]),
            config.window_bins,
            config.step_bins,
        )
        return PreparedParticipant(
            participant=str(f["participant"]),
            config=config,
            blocks=blocks,
            windows=windows,
            angle_error=f["angle_error"],
            velocity=f["velocity"],
            velocity_lag=f["velocity_lag"],
            pc_scores=f["pc_scores"],
            pca=PcaModel(
                mean=f["pca_mean"],
                components=f["pca_components"],
                explained_pct=f["pca_explained"],
                n_reference_bins=int(f["pca_n_reference"]),
            ),
            reference_sessions=tuple(int(v) for v in f["reference_sessions"]),
            reference_bins=f["reference_bins"],
            reference_candidate_bins=candidate,
            reference_candidate_ae_nan=n_ref_nan,
            n_features=n_features,
            zscore_audit=ZscoreAudit(first_zero, floored, total, float(f["zscore_max_first"])),
        )
