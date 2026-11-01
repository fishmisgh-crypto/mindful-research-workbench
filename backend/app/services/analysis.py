"""Cached window-level analysis results (KLD and median AE)."""

import threading
from pathlib import Path
from typing import Any

from app.services.dataset import DatasetNotFound
from mindful.runs import ensure_analysis

_lock = threading.Lock()


def get_analysis(
    data_dir: Path, processed_dir: Path, participant: str, preset: str
) -> dict[str, Any]:
    if not (data_dir / participant).is_dir():
        raise DatasetNotFound(f"participant folder not found: {data_dir / participant}")
    with _lock:
        return ensure_analysis(data_dir, processed_dir, participant, preset)
