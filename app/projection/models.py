from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class FieldRule(BaseModel):
    path: str
    from_field: Optional[str] = None
    normalize: Optional[str] = None
    required: bool = False


class ProjectionPlan(BaseModel):
    fields: list[FieldRule]

    include_confidence: bool = False
    include_provenance: bool = False
    include_quality: bool = False
    include_audit: bool = False
    include_conflicts: bool = False
    include_normalization_report: bool = False
    include_validation: bool = False

    on_missing: str = "null"
    identity_warning_threshold: float = 0.50


class ProjectionResult(BaseModel):
    output: Dict[str, Any]
    missing_events: List[Dict[str, Any]] = []
