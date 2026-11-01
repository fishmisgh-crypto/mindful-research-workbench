"""Cached preprocessing diagnostics. Recomputed only when the dataset or config changes."""

import json
import logging
import threading
from pathlib import Path
from typing import Any

from app.services.dataset import DatasetNotFound
from mindful.io.inventory import fingerprint
from mindful.preprocess.run import output_stem, run_and_save

log = logging.getLogger(__name__)
_lock = threading.Lock()


def get_diagnostics(
    data_dir: Path, processed_dir: Path, participant: str, preset: str
) -> dict[str, Any]:
    if not (data_dir / participant).is_dir():
        raise DatasetNotFound(f"participant folder not found: {data_dir / participant}")
    out_dir = processed_dir / "preprocess"
    path = output_stem(out_dir, participant, preset).with_suffix(".json")
    with _lock:
        current = fingerprint(data_dir)
        try:
            cached: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
            if cached.get("dataset_fingerprint") == current:
                return cached
        except (OSError, ValueError):
            pass
        log.info("Preprocessing %s with preset %s", participant, preset)
        out_dir.mkdir(parents=True, exist_ok=True)
        return run_and_save(data_dir, participant, preset, out_dir)
