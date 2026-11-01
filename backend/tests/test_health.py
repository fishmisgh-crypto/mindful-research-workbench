from pathlib import Path

from fastapi.testclient import TestClient

from app.api.health import detect_dataset
from app.core.settings import Settings, get_settings
from app.main import create_app


def client_with_data_dir(data_dir: Path) -> TestClient:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(data_dir=data_dir)
    return TestClient(app)


def test_health_reports_missing_dataset(tmp_path: Path) -> None:
    response = client_with_data_dir(tmp_path / "absent").get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["dataset"]["state"] == "missing"
    assert body["last_analysis_run"] is None


def test_detect_dataset_requires_both_participants(tmp_path: Path) -> None:
    (tmp_path / "T5").mkdir()
    status = detect_dataset(tmp_path)
    assert status.state == "missing"
    assert status.participant_folders == ["T5"]
    assert "T11" in status.message


def test_detect_dataset_present(tmp_path: Path) -> None:
    (tmp_path / "T5").mkdir()
    (tmp_path / "T11").mkdir()
    assert detect_dataset(tmp_path).state == "present"
