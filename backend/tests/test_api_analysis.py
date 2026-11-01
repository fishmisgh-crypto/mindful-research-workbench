"""SYNTHETIC — NOT STUDY DATA. Analysis endpoint."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.settings import Settings, get_settings
from app.main import create_app
from mindful import analysis as analysis_module
from mindful.analysis import AnalysisConfig
from mindful.preprocess import config as config_module
from mindful.preprocess.config import PreprocessConfig
from tests.synthetic import write_dataset

SMALL = PreprocessConfig(zscore_window_bins=50, window_bins=120, step_bins=30)


@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    write_dataset(tmp_path / "data", {"T5": {1: (1, 2), 2: (1,), 3: (1,)}}, n_bins=900, n_trials=8)
    monkeypatch.setitem(config_module.PRESETS, "upstream", SMALL)
    monkeypatch.setitem(
        analysis_module.ANALYSIS_PRESETS,
        "upstream",
        AnalysisConfig("upstream", SMALL, "uncentered_second_moment"),
    )
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(
        data_dir=tmp_path / "data", processed_dir=tmp_path / "processed"
    )
    return TestClient(app)


def test_window_table_and_summaries(client: TestClient) -> None:
    body = client.get("/api/analysis/T5?feature_set=extended9").json()
    assert body["kld_direction"] == "D_KL(P_reference || P_current)"
    assert set(body["summaries"]) == {"pca5", "extended9", "velocity2", "velocity4"}
    w = body["windows"]
    assert len(w["kld"]) == body["summaries"]["extended9"]["n_windows"]
    ends = [i for i, r in enumerate(w["reason"]) if r == "session_end"]
    assert ends and all(w["kld"][i] is None and w["median_ae"][i] is None for i in ends)


def test_windows_can_be_omitted(client: TestClient) -> None:
    assert client.get("/api/analysis/T5?include_windows=false").json()["windows"] is None


def test_bad_inputs_rejected(client: TestClient) -> None:
    assert client.get("/api/analysis/T5?feature_set=pca9").status_code == 422
    assert client.get("/api/analysis/T11").status_code == 404


def test_csv_export_has_one_row_per_window(client: TestClient) -> None:
    response = client.get("/api/exports/T5.csv?feature_set=extended9")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment" in response.headers["content-disposition"]
    lines = response.text.strip().split("\n")
    header = lines[0].split(",")
    assert header[:4] == ["participant", "preset", "feature_set", "config_digest"]
    assert "kld_nats" in header and "median_angular_error_deg" in header
    n_windows = client.get("/api/analysis/T5?feature_set=extended9").json()["summaries"][
        "extended9"
    ]["n_windows"]
    assert len(lines) - 1 == n_windows
    rows = [dict(zip(header, line.split(","), strict=True)) for line in lines[1:]]
    session_end = [r for r in rows if r["status"] == "session_end"]
    assert session_end
    assert all(r["kld_nats"] == "" and r["median_angular_error_deg"] == "" for r in session_end)
