"""SYNTHETIC — NOT STUDY DATA. Preprocessing diagnostics endpoint."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.settings import Settings, get_settings
from app.main import create_app
from app.services import preprocess as preprocess_service
from mindful.preprocess import config as config_module
from mindful.preprocess.config import PreprocessConfig
from tests.synthetic import write_dataset

SMALL = PreprocessConfig(zscore_window_bins=50, window_bins=120, step_bins=30)


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    write_dataset(tmp_path / "data", {"T5": {1: (1, 2), 2: (1,), 3: (1,)}}, n_bins=600, n_trials=6)
    monkeypatch.setitem(config_module.PRESETS, "upstream", SMALL)
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(
        data_dir=tmp_path / "data", processed_dir=tmp_path / "processed"
    )
    return TestClient(app)


def test_diagnostics_returned_and_cached(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    first = client.get("/api/preprocess/T5")
    assert first.status_code == 200
    body = first.json()
    assert body["preset"] == "upstream"
    assert body["reference"]["sessions"] == [1, 2]
    assert body["pca"]["explained_pct_sum"] == pytest.approx(100.0)

    def fail(*_: object) -> None:
        raise AssertionError("should have used the cache")

    monkeypatch.setattr(preprocess_service, "run_and_save", fail)
    assert client.get("/api/preprocess/T5").json()["config_digest"] == body["config_digest"]


def test_unknown_participant_and_preset_rejected(client: TestClient) -> None:
    assert client.get("/api/preprocess/T9").status_code == 422
    assert client.get("/api/preprocess/T5?preset=fast").status_code == 422


def test_missing_participant_folder_is_404(client: TestClient) -> None:
    assert client.get("/api/preprocess/T11").status_code == 404
