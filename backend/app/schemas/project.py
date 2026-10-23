from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


ConstructionType = Literal[
    "Residential", "Commercial", "Industrial", "Road/Highway", "Infrastructure", "Other"
]
ProjectStatus = Literal["Planning", "Active", "On Hold", "Completed"]


class ProjectPayload(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    code: str | None = Field(default=None, max_length=50)
    description: str | None = Field(default=None, max_length=5000)
    construction_type: ConstructionType
    project_manager: str | None = Field(default=None, max_length=120)
    site_address: str = Field(min_length=1, max_length=255)
    city: str = Field(min_length=1, max_length=100)
    state: str = Field(min_length=1, max_length=100)
    pin_code: str | None = Field(default=None, max_length=20)
    status: ProjectStatus
    start_date: date | None = None
    expected_completion_date: date | None = None
    budget: Decimal | None = Field(default=None, ge=0, max_digits=15, decimal_places=2)
    number_of_workers: int | None = Field(default=None, ge=0)
    safety_officer: str | None = Field(default=None, max_length=120)
    safety_notes: str | None = Field(default=None, max_length=5000)

    @model_validator(mode="after")
    def validate_dates(self):
        if self.start_date and self.expected_completion_date and self.expected_completion_date < self.start_date:
            raise ValueError("Expected completion date cannot be before the start date.")
        return self


class ProjectResponse(ProjectPayload):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime


class ProjectList(BaseModel):
    items: list[ProjectResponse]
    total: int
