from typing import Any, Dict


class ProvenanceTracker:
    """
    Build per-field provenance with source history, method, and resolution policy.
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

    def build(
        self,
        csv_data: Dict[str, Any],
        resume_data: Dict[str, Any],
        canonical: Dict[str, Any],
    ) -> Dict[str, Any]:
        provenance: Dict[str, Any] = {}
        merge_decisions = canonical.get("_merge_decisions", {})

        for field in canonical:
            if field in self.METADATA_FIELDS:
                continue

            decision = merge_decisions.get(field, {})
            sources = decision.get("sources") or self._infer_sources(
                field, csv_data, resume_data
            )

            if len(sources) > 1:
                method = "merge"
            elif sources:
                method = (
                    "structured_import"
                    if sources[0] == "recruiter_csv"
                    else "extraction"
                )
            else:
                method = "missing"

            provenance[field] = {
                "sources": sources,
                "method": method,
                "resolution_policy": decision.get("resolution_policy"),
            }

        return provenance

    def _infer_sources(
        self,
        field: str,
        csv_data: Dict[str, Any],
        resume_data: Dict[str, Any],
    ) -> list[str]:
        sources = []
        if self._field_present(field, csv_data):
            sources.append("recruiter_csv")
        if self._field_present(field, resume_data):
            sources.append("resume_pdf")
        return sources

    @staticmethod
    def _field_present(field: str, data: Dict[str, Any]) -> bool:
        if field not in data:
            return False
        value = data.get(field)
        if value is None:
            return False
        if isinstance(value, (list, dict, str)) and not value:
            return False
        return True
