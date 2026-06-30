from typing import Any, Dict, List


class QualityReport:
    CORE_FIELDS = [
        "candidate_id",
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

    def generate(
        self,
        canonical: Dict[str, Any],
        confidence_scores: Dict[str, float],
    ) -> Dict[str, Any]:
        missing_fields = self._missing_fields(canonical)
        conflicts_detected = len(canonical.get("conflict_report", []))
        source_count = canonical.get("source_count", 0)

        completeness_score = self._completeness_score(
            missing_fields,
            len(self.CORE_FIELDS),
        )
        consistency_score = self._consistency_score(conflicts_detected)
        trust_score = self._trust_score(confidence_scores)
        quality_score = round(
            (completeness_score + consistency_score + trust_score) / 3
        )

        return {
            "quality_score": quality_score,
            "completeness_score": completeness_score,
            "consistency_score": consistency_score,
            "trust_score": trust_score,
            "missing_fields": missing_fields,
            "conflicts_detected": conflicts_detected,
            "source_count": source_count,
        }

    def _missing_fields(self, canonical: Dict[str, Any]) -> List[str]:
        missing = []
        for field in self.CORE_FIELDS:
            if not self._is_present(canonical.get(field)):
                missing.append(field)
        return missing

    @staticmethod
    def _is_present(value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, (list, dict, str)) and not value:
            return False
        return True

    @staticmethod
    def _completeness_score(
        missing_fields: List[str],
        total_fields: int,
    ) -> int:
        if total_fields == 0:
            return 0
        present = total_fields - len(missing_fields)
        return round((present / total_fields) * 100)

    @staticmethod
    def _consistency_score(conflicts_detected: int) -> int:
        penalty = min(conflicts_detected * 12, 100)
        return max(0, 100 - penalty)

    @staticmethod
    def _trust_score(confidence_scores: Dict[str, float]) -> int:
        if not confidence_scores:
            return 0
        average = sum(confidence_scores.values()) / len(confidence_scores)
        return round(average * 100)
