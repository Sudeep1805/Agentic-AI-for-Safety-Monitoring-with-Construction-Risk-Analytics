
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class DetectionResponse(BaseModel):
    class_id: int
    class_name: str
    confidence: float
    bbox: list[float]


class HazardResponse(BaseModel):
    hazard: str
    confidence: float
    penalty: int
    description: str


class UploadResponse(BaseModel):
    id: str
    original_filename: str
    content_type: str
    size_bytes: int
    width: int
    height: int
    sha256: str
    site_context: str | None
    created_at: datetime
    image_url: str
    upload_status: Literal["saved"] = "saved"
    analysis_status: Literal["completed", "unavailable"] = "unavailable"
    analysis_message: str = (
        "Analysis unavailable. Detection has not been run for this response."
    )
    detections: list[DetectionResponse] = Field(default_factory=list)
    risk_score: int | None = None
    risk_level: Literal["Low", "Medium", "High"] | None = None
    hazard_count: int = 0
    hazards: list[HazardResponse] = Field(default_factory=list)


class UploadList(BaseModel):
    items: list[UploadResponse]
    total: int
