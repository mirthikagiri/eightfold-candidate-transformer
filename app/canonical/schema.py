from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Location(BaseModel):
    city: Optional[str] = None
    country: Optional[str] = None


class FieldProvenance(BaseModel):
    value: Any = None
    sources: List[str] = Field(default_factory=list)
    method: str = "extraction"
    resolution_policy: Optional[str] = None


class ConflictEntry(BaseModel):
    field: str
    candidates: List[Any]
    selected: Any
    reason: str


class QualityReportData(BaseModel):
    quality_score: int = 0
    completeness_score: int = 0
    consistency_score: int = 0
    trust_score: int = 0
    missing_fields: List[str] = Field(default_factory=list)
    conflicts_detected: int = 0
    source_count: int = 0


class Candidate(BaseModel):
    candidate_id: Optional[str] = None
    full_name: Optional[str] = None

    emails: List[str] = Field(default_factory=list)
    phones: List[str] = Field(default_factory=list)

    location: Optional[Location] = None
    links: List[str] = Field(default_factory=list)

    headline: Optional[str] = None
    years_experience: Optional[float] = None

    skills: List[str] = Field(default_factory=list)

    experience: List[dict] = Field(default_factory=list)
    education: List[dict] = Field(default_factory=list)

    provenance: Dict[str, Any] = Field(default_factory=dict)
    confidence: Dict[str, float] = Field(default_factory=dict)

    overall_confidence: Optional[float] = None

    quality_report: Dict[str, Any] = Field(default_factory=dict)
    conflict_report: List[Dict[str, Any]] = Field(default_factory=list)

    source_count: int = 0
    identity: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "allow"}


def validate_canonical(data: Dict[str, Any]) -> Candidate:
    """Validate a canonical record against the schema without mutating it."""
    return Candidate.model_validate(data)
