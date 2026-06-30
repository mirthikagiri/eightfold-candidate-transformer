from typing import Any, Dict, List


class AuditTrail:
    """
    Generate detailed audit metadata for every merged field.
    """

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

    FIELD_NORMALIZATIONS = {
        "phones": ["E164"],
        "emails": ["lowercase"],
        "skills": ["canonical"],
        "location": ["location_parse"],
    }

    def generate(
        self,
        canonical: Dict[str, Any],
        confidence_scores: Dict[str, float],
    ) -> Dict[str, Any]:
        audit: Dict[str, Any] = {}
        merge_decisions = canonical.get("_merge_decisions", {})

        for field in canonical:
            if field in self.METADATA_FIELDS:
                continue

            decision = merge_decisions.get(field, {})
            candidate_values = decision.get("candidate_values") or [
                {
                    "source": decision.get("selected_source"),
                    "value": decision.get("selected"),
                    "status": "valid",
                }
            ]

            selected_value = (
                canonical.get(field)
                if field in canonical
                else decision.get("selected")
            )

            audit[field] = {
                "selected_value": selected_value,
                "selected_source": decision.get("selected_source"),
                "candidate_values": candidate_values,
                "resolution_policy": decision.get("resolution_policy"),
                "confidence": confidence_scores.get(field, 0.0),
                "normalizations": self._normalizations_for(field),
            }

        return audit

    def _normalizations_for(self, field: str) -> List[str]:
        return self.FIELD_NORMALIZATIONS.get(field, [])
