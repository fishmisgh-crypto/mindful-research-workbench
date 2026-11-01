"""Health check: service liveness, library versions and dataset presence.

Dataset detection here is a shallow directory check only. Parsing and
validation of MATLAB files belongs to Phase 2.
"""

import platform
from pathlib import Path
from typing import Annotated

import fastapi
import numpy
import scipy
from fastapi import APIRouter, Depends

from app.core.settings import Settings, get_settings
from app.models.health import DatasetStatus, HealthResponse, Versions

router = APIRouter(tags=["health"])

EXPECTED_PARTICIPANTS = ("T5", "T11")


def detect_dataset(data_dir: Path) -> DatasetStatus:
    """Report whether the extracted dataset folder and participant folders exist."""
    if not data_dir.is_dir():
        return DatasetStatus(
            state="missing",
            configured_path=str(data_dir),
            participant_folders=[],
            message="Dataset folder not found. Download MINDFUL_Data.zip from Dryad "
            "(doi:10.5061/dryad.n2z34tn5s) and extract it to this path.",
        )
    found = sorted(p.name for p in data_dir.iterdir() if p.is_dir())
    missing = [p for p in EXPECTED_PARTICIPANTS if p not in found]
    if missing:
        return DatasetStatus(
            state="missing",
            configured_path=str(data_dir),
            participant_folders=found,
            message=f"Folder exists but participant folder(s) {', '.join(missing)} not found.",
        )
    return DatasetStatus(
        state="present",
        configured_path=str(data_dir),
        participant_folders=found,
        message="Participant folders found. Contents not yet validated (Phase 2).",
    )


@router.get("/api/health", response_model=HealthResponse)
def health(settings: Annotated[Settings, Depends(get_settings)]) -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="mindful-workbench",
        versions=Versions(
            python=platform.python_version(),
            numpy=numpy.__version__,
            scipy=scipy.__version__,
            fastapi=fastapi.__version__,
        ),
        dataset=detect_dataset(settings.data_dir),
        upstream_reference_present=(settings.upstream_dir / "utils" / "MINDFUL.m").is_file(),
        last_analysis_run=None,
    )
