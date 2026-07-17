from __future__ import annotations

import uuid
from datetime import date
from typing import List

from pydantic import BaseModel, ConfigDict, Field


class PatientSearchParams(BaseModel):
    """Search parameters for patient search (D-15, D-17, D-19, D-20)."""

    q: str = Field(..., min_length=4, max_length=200)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=100)
    status: str | None = None
    gender: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    state: str | None = None
    city: str | None = None


class PatientSearchResult(BaseModel):
    """A single patient search result with optional relevance score."""

    id: str
    mrn: str
    first_name: str
    last_name: str
    date_of_birth: date
    gender: str
    phone: str
    status: str
    relevance_score: float | None = None

    model_config = ConfigDict(from_attributes=True)


class PatientSearchResponse(BaseModel):
    """Paginated search response."""

    results: List[PatientSearchResult]
    total: int
    page: int
    page_size: int
    total_pages: int


class TypeaheadResult(BaseModel):
    """Lightweight typeahead result for autocomplete."""

    id: str
    mrn: str
    first_name: str
    last_name: str
    status: str
