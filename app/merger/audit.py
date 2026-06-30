from typing import Any, Dict


class AuditTrail:
    """
    Generate detailed audit metadata for every merged field.
    """

    def generate(
        self,
        canonical: Dict[str, Any],
        confidence_scores: Dict[str, float],
    ) -> Dict[str, Any]:
        audit: Dict[str, Any] = {}
        merge_decisions = canonical.get("_merge_decisions", {})
        metadata_fields = {
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
        }

        for field in canonical:
            if field in metadata_fields:
                continue

            decision = merge_decisions.get(field, {})
            audit[field] = {
                "selected_source": decision.get("selected_source"),
                "competing_values": decision.get("competing_values", []),
                "resolution_policy": decision.get(
                    "resolution_policy",
                    decision.get("policy"),
                ),
                "confidence": confidence_scores.get(field, 0.0),
            }

        return audit
