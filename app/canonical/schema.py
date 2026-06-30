from pydantic import BaseModel
from typing import List, Optional, Dict


class Location(BaseModel):
    city: Optional[str] = None
    country: Optional[str] = None


class Candidate(BaseModel):
    candidate_id: Optional[str] = None
    full_name: Optional[str] = None

    emails: List[str] = []
    phones: List[str] = []

    location: Optional[Location] = None

    headline: Optional[str] = None
    years_experience: Optional[float] = None

    skills: List[str] = []

    experience: List[dict] = []
    education: List[dict] = []

    provenance: Dict = {}
    confidence: Dict = {}

    overall_confidence: Optional[float] = None

    quality_report: Dict = {}