"""Reproduction report: published vs reproduced correlations for the whole run matrix."""

import threading
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException

from app.core.settings import Settings, get_settings
from mindful.io.block import LOAD_ERRORS
from mindful.reproduce import ensure_report

router = APIRouter(prefix="/api/report", tags=["report"])
_lock = threading.Lock()


@router.get("")
def report(settings: Annotated[Settings, Depends(get_settings)]) -> dict[str, Any]:
    """Cached until the dataset or the run matrix changes; first build takes minutes."""
    if not settings.data_dir.is_dir():
        detail = f"dataset folder not found: {settings.data_dir}"
        raise HTTPException(status_code=404, detail=detail)
    try:
        with _lock:
            return ensure_report(settings.data_dir, settings.processed_dir)
    except LOAD_ERRORS as exc:
        raise HTTPException(status_code=422, detail=f"report failed: {exc}") from exc
