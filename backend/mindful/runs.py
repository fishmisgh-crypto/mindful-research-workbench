"""Cache-aware orchestration: preprocessing and analysis results on disk.

Layout under the processed-data directory:
  preprocess/<participant>_<preset>_<preprocess digest>.json|.npz
  analysis/<participant>_<preset>_<analysis digest>.json

A cached file is reused only if it records the current dataset fingerprint.
"""

import json
from pathlib import Path
from typing import Any

from mindful.analysis import ANALYSIS_PRESETS, run_analysis
from mindful.io.inventory import fingerprint
from mindful.preprocess.pipeline import PreparedParticipant, load_prepared
from mindful.preprocess.run import output_stem, run_and_save


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data


def ensure_prepared(
    root: Path, processed: Path, participant: str, preset: str
) -> PreparedParticipant:
    out_dir = processed / "preprocess"
    stem = output_stem(out_dir, participant, preset)
    meta = _read_json(stem.with_suffix(".json"))
    if meta and meta.get("dataset_fingerprint") == fingerprint(root):
        try:
            return load_prepared(stem.with_suffix(".npz"))
        except (OSError, KeyError, ValueError):
            pass  # older npz layout or unreadable: rebuild below
    out_dir.mkdir(parents=True, exist_ok=True)
    run_and_save(root, participant, preset, out_dir)
    return load_prepared(stem.with_suffix(".npz"))


def analysis_path(processed: Path, participant: str, preset: str) -> Path:
    digest = ANALYSIS_PRESETS[preset].digest()
    return processed / "analysis" / f"{participant}_{preset}_{digest}.json"


def ensure_analysis(root: Path, processed: Path, participant: str, preset: str) -> dict[str, Any]:
    path = analysis_path(processed, participant, preset)
    current = fingerprint(root)
    cached = _read_json(path)
    if cached and cached.get("dataset_fingerprint") == current:
        return cached
    prep = ensure_prepared(root, processed, participant, preset)
    result = {"dataset_fingerprint": current, **run_analysis(prep, ANALYSIS_PRESETS[preset])}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result), encoding="utf-8")
    return result
