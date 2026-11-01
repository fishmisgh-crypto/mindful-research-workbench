"""Dataset inventory and per-block detail. No raw neural matrices are returned."""

import re
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.core.settings import Settings, get_settings
from app.models.dataset import BlockDetail, DatasetSummary
from app.services.dataset import DatasetNotFound, find_block, get_inventory
from mindful.io.block import LOAD_ERRORS
from mindful.io.detail import block_detail

router = APIRouter(prefix="/api/dataset", tags=["dataset"])

_NAMES = {
    "participant": re.compile(r"^(T11|T5)$"),
    "session": re.compile(r"^day_\d+$"),
    "block": re.compile(r"^Block_\d+$"),
}


@router.get("/summary", response_model=DatasetSummary)
def summary(settings: Annotated[Settings, Depends(get_settings)]) -> DatasetSummary:
    try:
        inventory = get_inventory(settings.data_dir, settings.processed_dir)
    except DatasetNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return DatasetSummary.model_validate(inventory)


@router.get("/{participant}/{session}/{block}", response_model=BlockDetail)
def detail(
    participant: str,
    session: str,
    block: str,
    settings: Annotated[Settings, Depends(get_settings)],
) -> BlockDetail:
    for label, value in (("participant", participant), ("session", session), ("block", block)):
        if not _NAMES[label].match(value):
            raise HTTPException(status_code=422, detail=f"invalid {label}: {value!r}")
    try:
        loaded = find_block(settings.data_dir, participant, session, block)
    except DatasetNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except LOAD_ERRORS as exc:
        raise HTTPException(status_code=422, detail=f"block cannot be loaded: {exc}") from exc
    return BlockDetail.model_validate(block_detail(loaded))
