"""Window-level CSV export: one row per 60-s window. Aggregates only, no neural data."""

import csv
import io
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from app.api.analysis import FeatureSet
from app.core.settings import Settings, get_settings
from app.services.analysis import get_analysis
from app.services.dataset import DatasetNotFound
from mindful.io.block import LOAD_ERRORS

router = APIRouter(prefix="/api/exports", tags=["exports"])

COLUMNS = (
    ("window", "window"),
    ("start_bin_0based", "start"),
    ("stop_bin_0based_inclusive", "stop"),
    ("session_index", "session_index"),
    ("trial_day", "day"),
    ("kld_nats", "kld"),
    ("kld_before_session_end_nan_nats", "kld_raw"),
    ("median_angular_error_deg", "median_ae"),
    ("status", "reason"),
    ("covariance_condition_number", "condition"),
)


@router.get("/{participant}.csv")
def export_windows(
    participant: Literal["T11", "T5"],
    settings: Annotated[Settings, Depends(get_settings)],
    preset: Annotated[Literal["upstream", "paper"], Query()] = "upstream",
    feature_set: Annotated[FeatureSet, Query()] = "pca5",
) -> Response:
    try:
        result = get_analysis(settings.data_dir, settings.processed_dir, participant, preset)
    except DatasetNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except LOAD_ERRORS as exc:
        raise HTTPException(status_code=422, detail=f"analysis failed: {exc}") from exc
    windows = result["feature_sets"][feature_set]["windows"]
    fixed = {
        "participant": participant,
        "preset": preset,
        "feature_set": feature_set,
        "config_digest": result["config_digest"],
    }
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow([*fixed, *(name for name, _ in COLUMNS)])
    for i in range(len(windows["window"])):
        row = [windows[key][i] for _, key in COLUMNS]
        writer.writerow([*fixed.values(), *("" if v is None else v for v in row)])
    filename = f"mindful_{participant}_{preset}_{feature_set}_{result['config_digest']}.csv"
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
