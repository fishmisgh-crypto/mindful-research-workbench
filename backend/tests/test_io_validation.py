"""SYNTHETIC — NOT STUDY DATA. Block checks, angular error and the inventory."""

import json
from pathlib import Path

import numpy as np
import scipy.io as sio

from mindful.io.block import load_block
from mindful.io.discovery import discover_participant
from mindful.io.inventory import build_inventory
from mindful.io.validation import validate_block, worst
from mindful.stats.angular import angle_between_deg
from tests.synthetic import write_block, write_dataset


def checks_by_id(root: Path, participant: str) -> dict[str, str]:
    block = load_block(discover_participant(root, participant).sessions[0].blocks[0])
    return {c.id: c.status for c in validate_block(block)}


def test_angle_between_known_values() -> None:
    a = np.array([[1.0, 0.0], [1.0, 0.0], [1.0, 0.0], [0.0, 0.0]])
    b = np.array([[1.0, 0.0], [0.0, 2.0], [-3.0, 0.0], [1.0, 1.0]])
    out = angle_between_deg(a, b)
    np.testing.assert_allclose(out[:3], [0.0, 90.0, 180.0], atol=1e-9)
    assert np.isnan(out[3])


def test_consistent_synthetic_block_passes(tmp_path: Path) -> None:
    write_block(tmp_path / "T11/day_1/Block_01")
    statuses = checks_by_id(tmp_path, "T11")
    assert statuses["feature_set"] == "pass"
    assert statuses["trial_bounds"] == "pass"
    assert statuses["ae_recomputed"] == "pass"
    assert statuses["labels_definition"] == "pass"
    assert "fail" not in statuses.values()


def test_spike_power_in_t5_is_flagged_d8(tmp_path: Path) -> None:
    write_block(tmp_path / "T5/day_1/Block_01", spike_power=True)
    assert checks_by_id(tmp_path, "T5")["feature_set"] == "warn"


def test_missing_spike_power_in_t11_fails(tmp_path: Path) -> None:
    write_block(tmp_path / "T11/day_1/Block_01", spike_power=False)
    assert checks_by_id(tmp_path, "T11")["feature_set"] == "fail"


def test_trial_past_block_end_fails(tmp_path: Path) -> None:
    folder = tmp_path / "T11/day_1/Block_01"
    write_block(folder, n_bins=300)
    task = {k: v for k, v in sio.loadmat(folder / "task.mat").items() if not k.startswith("__")}
    task["startStops"][-1, 1] = 301
    sio.savemat(folder / "task.mat", task)
    assert checks_by_id(tmp_path, "T11")["trial_bounds"] == "fail"


def test_worst_status_ordering() -> None:
    from mindful.io.validation import Check

    assert worst([Check("a", "pass", ""), Check("b", "warn", ""), Check("c", "info", "")]) == "warn"
    assert worst([]) == "pass"


def test_inventory_compares_with_documented_counts(tmp_path: Path) -> None:
    write_dataset(tmp_path, {"T5": {2121: (1, 2), 2126: (1,)}})
    inv = build_inventory(tmp_path)
    t5 = inv["participants"][0]
    checks = {c["id"]: c for c in t5["checks"]}
    assert t5["n_sessions"] == 2 and t5["n_blocks"] == 3
    assert checks["sessions"]["status"] == "warn"  # 2 observed vs 6 documented
    assert "2 observed, 6 documented" in checks["sessions"]["message"]
    assert checks["load"]["status"] == "pass"
    assert len(inv["content_digest_sha256"]) == 64


def test_inventory_contains_aggregates_only(tmp_path: Path) -> None:
    write_dataset(tmp_path, {"T11": {658: (5,)}}, n_bins=2000)
    text = json.dumps(build_inventory(tmp_path))
    assert len(text) < 20_000  # 2000 × 384 raw values would be far larger
    assert "nctx_mean_rate" in text
