from typing import Any, Dict, List, Set, Tuple


class ConfidenceScorer:
    SOURCE_WEIGHTS = {
        "resume_pdf": 0.90,
        "recruiter_csv": 0.80,
    }

    AGREEMENT_BONUS = 0.05
    VALIDATION_BONUS = 0.05
    CONFLICT_PENALTY = 0.10
    INVALID_SOURCE_PENALTY = 0.15
    MISSING_CRITICAL_PENALTY = 0.20

    CRITICAL_FIELDS = {"full_name", "emails", "phones"}

    SCORABLE_FIELDS = [
        "full_name",
        "emails",
        "phones",
        "location",
        "headline",
        "years_experience",
        "skills",
        "experience",
        "education",
        "links",
    ]

    METADATA_FIELDS = {
        "source_count",
        "conflict_report",
        "_merge_decisions",
        "provenance",
        "confidence",
        "overall_confidence",
        "quality_report",
        "_audit",
        "candidate_id",
        "identity",
        "normalization_report",
    }

    VALIDATED_FIELDS = {"phones", "emails"}

    def score_field(
        self,
        field_name: str,
        canonical: Dict[str, Any],
        csv_data: Dict[str, Any],
        resume_data: Dict[str, Any],
        conflict_fields: Set[str],
        uncertain_fields: Set[str],
        invalid_fields: Set[str],
    ) -> float:
        value = canonical.get(field_name)
        if not self._is_present(value):
            if field_name in self.CRITICAL_FIELDS:
                return 0.0
            return 0.0

        provenance = canonical.get("provenance", {}).get(field_name, {})
        sources = provenance.get("sources", [])

        if not sources:
            if field_name in self.CRITICAL_FIELDS:
                return round(max(0.0, 0.0), 2)
            return 0.0

        if len(sources) == 2:
            base = max(self.SOURCE_WEIGHTS.values())
        elif sources[0] == "resume_pdf":
            base = self.SOURCE_WEIGHTS["resume_pdf"]
        else:
            base = self.SOURCE_WEIGHTS["recruiter_csv"]

        score = base

        if len(sources) == 2 and field_name not in conflict_fields:
            score += self.AGREEMENT_BONUS

        if field_name in self.VALIDATED_FIELDS and self._value_validated(
            field_name, value
        ):
            score += self.VALIDATION_BONUS

        if field_name in conflict_fields:
            score -= self.CONFLICT_PENALTY

        if field_name in uncertain_fields or field_name in invalid_fields:
            score -= self.INVALID_SOURCE_PENALTY

        return round(max(0.0, min(1.0, score)), 2)

    def score_profile(
        self,
        canonical: Dict[str, Any],
        csv_data: Dict[str, Any],
        resume_data: Dict[str, Any],
    ) -> Tuple[Dict[str, float], float]:
        conflict_fields = {
            entry["field"] for entry in canonical.get("conflict_report", [])
        }
        uncertain_fields = set(
            (csv_data.get("_uncertain_fields") or [])
            + (resume_data.get("_uncertain_fields") or [])
        )
        invalid_fields = self._invalid_source_fields(
            canonical.get("normalization_report", [])
        )

        scores: Dict[str, float] = {}

        for field in self.SCORABLE_FIELDS:
            scores[field] = self.score_field(
                field,
                canonical,
                csv_data,
                resume_data,
                conflict_fields,
                uncertain_fields,
                invalid_fields,
            )

        for field in self.CRITICAL_FIELDS:
            if not self._is_present(canonical.get(field)):
                scores[field] = round(
                    max(0.0, scores.get(field, 0.0) - self.MISSING_CRITICAL_PENALTY),
                    2,
                )

        present_scores = [
            scores[field]
            for field in self.SCORABLE_FIELDS
            if self._is_present(canonical.get(field))
        ]

        if present_scores:
            overall = round(sum(present_scores) / len(present_scores), 2)
        else:
            overall = 0.0

        return scores, overall

    @staticmethod
    def _invalid_source_fields(
        normalization_report: List[Dict[str, Any]],
    ) -> Set[str]:
        invalid = set()
        for entry in normalization_report:
            if entry.get("status") == "invalid":
                field = entry.get("field", "")
                if field in {"phone", "phones"}:
                    invalid.add("phones")
                elif field in {"email", "emails"}:
                    invalid.add("emails")
                else:
                    invalid.add(field)
        return invalid

    @staticmethod
    def _value_validated(field_name: str, value: Any) -> bool:
        if field_name == "phones":
            return isinstance(value, list) and all(
                isinstance(phone, str) and phone.startswith("+") for phone in value
            )
        if field_name == "emails":
            return isinstance(value, list) and all(
                isinstance(email, str) and "@" in email for email in value
            )
        return False

    @staticmethod
    def _is_present(value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, (list, dict, str)) and not value:
            return False
        return True
