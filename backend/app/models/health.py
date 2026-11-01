"""Response schemas for the health endpoint."""

from typing import Literal

from pydantic import BaseModel

DatasetState = Literal["missing", "present"]


class DatasetStatus(BaseModel):
    state: DatasetState
    configured_path: str
    participant_folders: list[str]
    message: str


class Versions(BaseModel):
    python: str
    numpy: str
    scipy: str
    fastapi: str


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    versions: Versions
    dataset: DatasetStatus
    upstream_reference_present: bool
    last_analysis_run: str | None
