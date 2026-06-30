from typing import Any, Dict, List, Optional

from app.normalizers.skills import normalize_skills


class ProvenanceTracker:
    """
    Build per-field provenance with source history, method, resolution policy,
    and item-level traceability for collection fields.
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

    ITEM_LEVEL_FIELDS = {"phones", "emails", "skills", "experience", "education"}

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

            entry: Dict[str, Any] = {
                "sources": sources,
                "method": method,
                "resolution_policy": decision.get("resolution_policy"),
            }

            if field in self.ITEM_LEVEL_FIELDS:
                entry["items"] = self._build_items(
                    field,
                    canonical,
                    decision,
                    csv_data,
                    resume_data,
                )

            provenance[field] = entry

        return provenance

    def _build_items(
        self,
        field: str,
        canonical: Dict[str, Any],
        decision: Dict[str, Any],
        csv_data: Dict[str, Any],
        resume_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        if field in {"phones", "emails"}:
            return self._items_from_candidates(
                canonical.get(field, []),
                decision.get("candidate_values", []),
            )
        if field == "skills":
            return self._items_for_skills(
                canonical.get("skills", []),
                csv_data,
                resume_data,
            )
        if field in {"experience", "education"}:
            return self._items_for_entries(
                field,
                canonical.get(field, []),
                csv_data,
                resume_data,
            )
        return []

    @staticmethod
    def _items_from_candidates(
        selected_values: List[Any],
        candidate_values: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        for value in selected_values or []:
            matching_sources = sorted(
                {
                    candidate["source"]
                    for candidate in candidate_values
                    if candidate.get("status") == "valid"
                    and candidate.get("value") == value
                    and candidate.get("source")
                }
            )
            if len(matching_sources) == 1:
                items.append({"value": value, "source": matching_sources[0]})
            elif matching_sources:
                items.append({"value": value, "sources": matching_sources})
            else:
                items.append({"value": value, "source": None})
        return items

    @staticmethod
    def _items_for_skills(
        skills: List[str],
        csv_data: Dict[str, Any],
        resume_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        csv_skills = set(normalize_skills(csv_data.get("skills") or []))
        resume_skills = set(normalize_skills(resume_data.get("skills") or []))
        items: List[Dict[str, Any]] = []

        for skill in skills or []:
            in_csv = skill in csv_skills
            in_resume = skill in resume_skills
            if in_csv and in_resume:
                items.append(
                    {
                        "value": skill,
                        "sources": ["recruiter_csv", "resume_pdf"],
                    }
                )
            elif in_resume:
                items.append({"value": skill, "source": "resume_pdf"})
            elif in_csv:
                items.append({"value": skill, "source": "recruiter_csv"})
            else:
                items.append({"value": skill, "source": None})

        return items

    @staticmethod
    def _entry_key(entry: dict) -> tuple:
        return tuple(sorted((str(k), str(v)) for k, v in entry.items()))

    def _items_for_entries(
        self,
        field: str,
        entries: List[dict],
        csv_data: Dict[str, Any],
        resume_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        csv_entries = {
            self._entry_key(entry): entry
            for entry in (csv_data.get(field) or [])
            if isinstance(entry, dict)
        }
        resume_entries = {
            self._entry_key(entry): entry
            for entry in (resume_data.get(field) or [])
            if isinstance(entry, dict)
        }
        items: List[Dict[str, Any]] = []

        for entry in entries or []:
            if not isinstance(entry, dict):
                continue
            key = self._entry_key(entry)
            in_csv = key in csv_entries
            in_resume = key in resume_entries
            item: Dict[str, Any] = {"value": entry}
            if in_csv and in_resume:
                item["sources"] = ["recruiter_csv", "resume_pdf"]
            elif in_resume:
                item["source"] = "resume_pdf"
            elif in_csv:
                item["source"] = "recruiter_csv"
            else:
                item["source"] = None
            items.append(item)

        return items

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
