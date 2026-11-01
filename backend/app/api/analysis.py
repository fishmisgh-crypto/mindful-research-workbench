"""Window-level KLD and median angular error per participant, preset and feature set."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.settings import Settings, get_settings
from app.models.analysis import AnalysisResponse
from app.services.analysis import get_analysis
from app.services.dataset import DatasetNotFound
from mindful.io.block import LOAD_ERRORS

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

FeatureSet = Literal["pca5", "extended9", "velocity2", "velocity4"]


@router.get("/{participant}", response_model=AnalysisResponse)
def analysis(
    participant: Literal["T11", "T5"],
    settings: Annotated[Settings, Depends(get_settings)],
    preset: Annotated[Literal["upstream", "paper"], Query()] = "upstream",
    feature_set: Annotated[FeatureSet, Query()] = "pca5",
    include_windows: Annotated[bool, Query()] = True,
) -> AnalysisResponse:
    try:
        result = get_analysis(settings.data_dir, settings.processed_dir, participant, preset)
    except DatasetNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except LOAD_ERRORS as exc:
        raise HTTPException(status_code=422, detail=f"analysis failed: {exc}") from exc
    sets = result["feature_sets"]
    return AnalysisResponse.model_validate(
        {
            **{k: v for k, v in result.items() if k not in ("feature_sets", "dataset_fingerprint")},
            "feature_set": feature_set,
            "summaries": {name: fs["summary"] for name, fs in sets.items()},
            "windows": sets[feature_set]["windows"] if include_windows else None,
        }
    )
