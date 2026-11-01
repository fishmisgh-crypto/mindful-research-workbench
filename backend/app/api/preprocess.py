"""Preprocessing diagnostics per participant and preset."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.settings import Settings, get_settings
from app.models.preprocess import PreprocessDiagnostics
from app.services.dataset import DatasetNotFound
from app.services.preprocess import get_diagnostics
from mindful.io.block import LOAD_ERRORS

router = APIRouter(prefix="/api/preprocess", tags=["preprocess"])


@router.get("/{participant}", response_model=PreprocessDiagnostics)
def preprocess(
    participant: Literal["T11", "T5"],
    settings: Annotated[Settings, Depends(get_settings)],
    preset: Annotated[Literal["upstream", "paper"], Query()] = "upstream",
) -> PreprocessDiagnostics:
    try:
        diag = get_diagnostics(settings.data_dir, settings.processed_dir, participant, preset)
    except DatasetNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except LOAD_ERRORS as exc:
        raise HTTPException(status_code=422, detail=f"preprocessing failed: {exc}") from exc
    return PreprocessDiagnostics.model_validate(diag)
