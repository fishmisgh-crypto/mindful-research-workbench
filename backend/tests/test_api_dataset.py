"""SYNTHETIC — NOT STUDY DATA. Dataset API endpoints."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.settings import Settings, get_settings
from app.main import create_app
from app.services import dataset as dataset_service
from tests.synthetic import write_dataset


@pytest.fixture
def data_root(tmp_path: Path) -> Path:
    root = tmp_path / "MINDFUL_Data"
    write_dataset(root, {"T11": {658: (5, 7)}, "T5": {2121: (1,)}}, n_bins=500)
    return root


def client_for(data_dir: Path, processed: Path) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(
        data_dir=data_dir, processed_dir=processed
    )
    return TestClient(app)


def test_summary_lists_participants_sessions_blocks(data_root: Path, tmp_path: Path) -> None:
    body = client_for(data_root, tmp_path / "processed").get("/api/dataset/summary").json()
    ids = {p["id"]: p for p in body["participants"]}
    assert set(ids) == {"T11", "T5"}
    assert ids["T11"]["n_blocks"] == 2
    assert ids["T11"]["feature_counts"] == [384]
    assert ids["T5"]["feature_counts"] == [192]
    assert ids["T11"]["sessions"][0]["blocks"][0]["name"] == "Block_05"


def test_summary_is_cached_until_files_change(
    data_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = 0
    real = dataset_service.build_inventory

    def counting(root: Path) -> dict[str, object]:
        nonlocal calls
        calls += 1
        return real(root)

    monkeypatch.setattr(dataset_service, "build_inventory", counting)
    client = client_for(data_root, tmp_path / "processed")
    client.get("/api/dataset/summary")
    client.get("/api/dataset/summary")
    assert calls == 1
    (data_root / "T5/day_2121/Block_01/data.mat").write_bytes(
        (data_root / "T5/day_2121/Block_01/data.mat").read_bytes() + b"\0"
    )
    body = client.get("/api/dataset/summary").json()
    assert calls == 2
    t5_block = body["participants"][1]["sessions"][0]["blocks"][0]
    assert t5_block["status"] == "fail"  # the appended byte corrupts the file; reported, not raised
    assert t5_block["checks"][0]["id"] == "load"


def test_summary_404_without_dataset(tmp_path: Path) -> None:
    response = client_for(tmp_path / "absent", tmp_path / "p").get("/api/dataset/summary")
    assert response.status_code == 404


def test_block_detail_returns_aggregates(data_root: Path, tmp_path: Path) -> None:
    response = client_for(data_root, tmp_path / "p").get("/api/dataset/T11/day_658/Block_07")
    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["name"] == "Block_07"
    assert len(body["trials"]) == body["summary"]["n_trials"]
    assert body["trials"][0]["start"] >= 1
    assert len(body["channel_means"]["nctx"]) == 192
    assert len(body["channel_means"]["spikePower"]) == 192
    assert sum(body["ae_histogram"]["counts"]) > 0


@pytest.mark.parametrize(
    "path",
    [
        "/api/dataset/T9/day_658/Block_05",
        "/api/dataset/T11/..%2F..%2Fsecret/Block_05",
        "/api/dataset/T11/day_658/data.mat",
    ],
)
def test_block_detail_rejects_bad_names(data_root: Path, tmp_path: Path, path: str) -> None:
    assert client_for(data_root, tmp_path / "p").get(path).status_code in (404, 422)


def test_block_detail_404_for_unknown_block(data_root: Path, tmp_path: Path) -> None:
    response = client_for(data_root, tmp_path / "p").get("/api/dataset/T11/day_658/Block_99")
    assert response.status_code == 404
