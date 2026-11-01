"""Dataset inventory cache and block lookup for the API.

The inventory is rebuilt only when the .mat files change (path, size or mtime),
and stored as JSON under the processed-data directory.
"""

import json
import logging
import threading
from pathlib import Path
from typing import Any

from mindful.io.block import Block, load_block
from mindful.io.discovery import discover_participant
from mindful.io.inventory import SCHEMA_VERSION, build_inventory, fingerprint

log = logging.getLogger(__name__)
_lock = threading.Lock()

INVENTORY_FILE = "inventory.json"


class DatasetNotFound(LookupError):
    pass


def _read_cache(path: Path) -> dict[str, Any] | None:
    try:
        cached: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return cached


def get_inventory(data_dir: Path, processed_dir: Path) -> dict[str, Any]:
    """Return the cached inventory, rebuilding it if the dataset changed."""
    if not data_dir.is_dir():
        raise DatasetNotFound(f"dataset folder not found: {data_dir}")
    cache_path = processed_dir / INVENTORY_FILE
    with _lock:
        current = fingerprint(data_dir)
        cached = _read_cache(cache_path)
        if (
            cached
            and cached.get("fingerprint") == current
            and cached.get("schema_version") == SCHEMA_VERSION
            and cached.get("root") == str(data_dir)
        ):
            return cached
        log.info("Building dataset inventory for %s", data_dir)
        inventory = build_inventory(data_dir)
        processed_dir.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(inventory, indent=2), encoding="utf-8")
        return inventory


def find_block(data_dir: Path, participant: str, session: str, block: str) -> Block:
    """Load one block by participant id, session folder name and block folder name."""
    if not (data_dir / participant).is_dir():
        raise DatasetNotFound(f"unknown participant {participant}")
    for s in discover_participant(data_dir, participant).sessions:
        if s.name != session:
            continue
        for ref in s.blocks:
            if ref.name == block:
                return load_block(ref)
    raise DatasetNotFound(f"no block {participant}/{session}/{block}")
