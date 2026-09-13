"""Pydantic schemas for creating, updating, and returning cases."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


CaseStatus = Literal["open", "in_progress", "resolved", "closed"]
CasePriority = Literal["low", "medium", "high", "critical"]


class CaseCreate(BaseModel):
    """Fields accepted when creating a case."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    case_number: str = Field(min_length=1, max_length=50)
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    status: CaseStatus
    priority: CasePriority


class CaseUpdate(BaseModel):
    """Optional fields accepted when partially updating a case."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    case_number: str | None = Field(default=None, min_length=1, max_length=50)
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    status: CaseStatus | None = None
    priority: CasePriority | None = None


class CaseResponse(BaseModel):
    """Complete case data returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    case_number: str
    title: str
    description: str | None
    status: CaseStatus
    priority: CasePriority
    created_at: datetime
    updated_at: datetime