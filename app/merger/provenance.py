from typing import Any, Dict


class ProvenanceTracker:
    """
    Build per-field provenance with value, sources, method, and resolution policy.
    """

    def build(
        self,
        csv_data: Dict[str, Any],
        resume_data: Dict[str, Any],
        canonical: Dict[str, Any],
    ) -> Dict[str, Any]:
        provenance: Dict[str, Any] = {}
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

        for field, value in canonical.items():
            if field in metadata_fields:
                continue

            decision = merge_decisions.get(field, {})
            sources = decision.get("sources") or self._infer_sources(
                field, csv_data, resume_data
            )

            if len(sources) > 1:
                method = "merged"
            elif sources:
                method = (
                    "structured_import"
                    if sources[0] == "recruiter_csv"
                    else "extraction"
                )
            else:
                method = "missing"

            provenance[field] = {
                "value": value,
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
