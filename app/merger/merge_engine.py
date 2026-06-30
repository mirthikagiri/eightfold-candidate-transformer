from typing import Any, Dict, List, Optional, Tuple

from app.normalizers.email import normalize_email
from app.normalizers.location import location_to_string, normalize_location
from app.normalizers.phone import normalize_phone
from app.normalizers.skills import normalize_skills


class MergeEngine:
    """
    Deterministic merge of candidate data from multiple sources into
    a canonical candidate record with conflict tracking.
    """

    RESUME_SOURCE = "resume_pdf"
    CSV_SOURCE = "recruiter_csv"

    def merge(
        self,
        csv_data: Dict[str, Any],
        resume_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        conflict_report: List[Dict[str, Any]] = []
        merge_decisions: Dict[str, Dict[str, Any]] = {}

        canonical: Dict[str, Any] = {}

        canonical["full_name"], decision = self._merge_scalar(
            csv_data.get("full_name"),
            resume_data.get("full_name"),
            prefer=self.RESUME_SOURCE,
            policy="resume_priority",
        )
        merge_decisions["full_name"] = decision
        self._record_scalar_conflict(
            conflict_report, "full_name", decision
        )

        canonical["headline"], decision = self._merge_scalar(
            csv_data.get("headline"),
            resume_data.get("headline"),
            prefer=self.RESUME_SOURCE,
            policy="resume_priority",
        )
        merge_decisions["headline"] = decision
        self._record_scalar_conflict(
            conflict_report, "headline", decision
        )

        canonical["years_experience"], decision = self._merge_scalar(
            csv_data.get("years_experience"),
            resume_data.get("years_experience"),
            prefer=self.RESUME_SOURCE,
            policy="resume_priority",
        )
        merge_decisions["years_experience"] = decision
        self._record_scalar_conflict(
            conflict_report, "years_experience", decision
        )

        canonical["location"], decision = self._merge_location(
            csv_data.get("location"),
            resume_data.get("location"),
        )
        merge_decisions["location"] = decision
        self._record_scalar_conflict(
            conflict_report,
            "location",
            decision,
            compare_key="display",
        )

        canonical["emails"] = self._merge_emails(
            csv_data.get("emails", []),
            resume_data.get("emails", []),
        )
        merge_decisions["emails"] = {
            "policy": "union_dedupe",
            "sources": self._list_sources(
                csv_data.get("emails", []),
                resume_data.get("emails", []),
            ),
            "competing_values": [],
        }

        canonical["phones"] = self._merge_phones(
            csv_data.get("phones", []),
            resume_data.get("phones", []),
        )
        merge_decisions["phones"] = {
            "policy": "union_dedupe",
            "sources": self._list_sources(
                csv_data.get("phones", []),
                resume_data.get("phones", []),
            ),
            "competing_values": [],
        }

        canonical["skills"] = normalize_skills(
            list(
                set(
                    (csv_data.get("skills") or [])
                    + (resume_data.get("skills") or [])
                )
            )
        )
        merge_decisions["skills"] = {
            "policy": "union_canonical",
            "sources": self._list_sources(
                csv_data.get("skills", []),
                resume_data.get("skills", []),
            ),
            "competing_values": [],
        }

        canonical["links"] = self._merge_links(
            csv_data.get("links", []),
            resume_data.get("links", []),
        )
        merge_decisions["links"] = {
            "policy": "union_dedupe",
            "sources": self._list_sources(
                csv_data.get("links", []),
                resume_data.get("links", []),
            ),
            "competing_values": [],
        }

        canonical["experience"] = self._merge_unique_entries(
            csv_data.get("experience", []),
            resume_data.get("experience", []),
        )
        merge_decisions["experience"] = {
            "policy": "merge_unique",
            "sources": self._list_sources(
                csv_data.get("experience", []),
                resume_data.get("experience", []),
            ),
            "competing_values": [],
        }

        canonical["education"] = self._merge_unique_entries(
            csv_data.get("education", []),
            resume_data.get("education", []),
        )
        merge_decisions["education"] = {
            "policy": "merge_unique",
            "sources": self._list_sources(
                csv_data.get("education", []),
                resume_data.get("education", []),
            ),
            "competing_values": [],
        }

        active_sources = sum(
            1 for source in (csv_data, resume_data) if self._has_content(source)
        )
        canonical["source_count"] = max(active_sources, 1)
        canonical["conflict_report"] = conflict_report
        canonical["_merge_decisions"] = merge_decisions

        return canonical

    def _merge_scalar(
        self,
        csv_value: Any,
        resume_value: Any,
        prefer: str,
        policy: str,
    ) -> Tuple[Any, Dict[str, Any]]:
        csv_present = self._is_present(csv_value)
        resume_present = self._is_present(resume_value)

        competing = []
        if csv_present:
            competing.append(csv_value)
        if resume_present:
            competing.append(resume_value)

        if prefer == self.RESUME_SOURCE:
            selected = resume_value if resume_present else csv_value
            selected_source = (
                self.RESUME_SOURCE if resume_present else self.CSV_SOURCE
            )
        else:
            selected = csv_value if csv_present else resume_value
            selected_source = (
                self.CSV_SOURCE if csv_present else self.RESUME_SOURCE
            )

        sources = []
        if csv_present:
            sources.append(self.CSV_SOURCE)
        if resume_present:
            sources.append(self.RESUME_SOURCE)

        decision = {
            "selected": selected,
            "selected_source": selected_source,
            "competing_values": competing,
            "resolution_policy": policy,
            "sources": sources,
        }
        return selected, decision

    def _merge_location(
        self,
        csv_value: Any,
        resume_value: Any,
    ) -> Tuple[Optional[Dict[str, Optional[str]]], Dict[str, Any]]:
        csv_location = normalize_location(csv_value)
        resume_location = normalize_location(resume_value)

        csv_present = csv_location is not None
        resume_present = resume_location is not None

        competing = []
        if csv_present:
            competing.append(location_to_string(csv_location))
        if resume_present:
            competing.append(location_to_string(resume_location))

        if resume_present:
            selected = resume_location
            selected_source = self.RESUME_SOURCE
            policy = "highest_confidence"
        elif csv_present:
            selected = csv_location
            selected_source = self.CSV_SOURCE
            policy = "highest_confidence"
        else:
            selected = None
            selected_source = None
            policy = "highest_confidence"

        sources = []
        if csv_present:
            sources.append(self.CSV_SOURCE)
        if resume_present:
            sources.append(self.RESUME_SOURCE)

        decision = {
            "selected": location_to_string(selected) if selected else None,
            "selected_source": selected_source,
            "competing_values": [value for value in competing if value],
            "resolution_policy": policy,
            "sources": sources,
            "display": location_to_string(selected) if selected else None,
        }
        return selected, decision

    def _merge_emails(
        self,
        csv_emails: List[str],
        resume_emails: List[str],
    ) -> List[str]:
        merged: Dict[str, str] = {}
        for email in csv_emails + resume_emails:
            normalized = normalize_email(email)
            if normalized:
                merged[normalized] = normalized
        return sorted(merged.values())

    def _merge_phones(
        self,
        csv_phones: List[str],
        resume_phones: List[str],
    ) -> List[str]:
        merged: Dict[str, str] = {}
        for phone in csv_phones + resume_phones:
            if not phone:
                continue
            normalized = normalize_phone(phone)
            key = normalized or phone.strip()
            merged[key] = normalized or phone.strip()
        return sorted(merged.values())

    def _merge_links(
        self,
        csv_links: List[str],
        resume_links: List[str],
    ) -> List[str]:
        merged = {}
        for link in csv_links + resume_links:
            if link:
                merged[link.strip().lower()] = link.strip()
        return sorted(merged.values())

    def _merge_unique_entries(
        self,
        csv_entries: List[dict],
        resume_entries: List[dict],
    ) -> List[dict]:
        seen = set()
        merged = []
        for entry in csv_entries + resume_entries:
            if not isinstance(entry, dict):
                continue
            key = tuple(sorted((str(k), str(v)) for k, v in entry.items()))
            if key in seen:
                continue
            seen.add(key)
            merged.append(entry)
        return merged

    def _record_scalar_conflict(
        self,
        conflict_report: List[Dict[str, Any]],
        field: str,
        decision: Dict[str, Any],
        compare_key: str = "selected",
    ) -> None:
        competing = decision.get("competing_values", [])
        unique_values = []
        for value in competing:
            if value not in unique_values:
                unique_values.append(value)

        if len(unique_values) <= 1:
            return

        normalized = [self._normalize_compare_value(value) for value in unique_values]
        if len(set(normalized)) == 1:
            return

        conflict_report.append(
            {
                "field": field,
                "candidates": unique_values,
                "selected": decision.get(compare_key, decision.get("selected")),
                "reason": decision.get("resolution_policy", "unknown"),
            }
        )

    def _list_sources(
        self,
        csv_values: List[Any],
        resume_values: List[Any],
    ) -> List[str]:
        sources = []
        if csv_values:
            sources.append(self.CSV_SOURCE)
        if resume_values:
            sources.append(self.RESUME_SOURCE)
        return sources

    @staticmethod
    def _normalize_compare_value(value: Any) -> str:
        if isinstance(value, dict):
            return str(sorted(value.items()))
        return str(value).strip().lower()

    @staticmethod
    def _is_present(value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, (list, dict, str)) and not value:
            return False
        return True

    @staticmethod
    def _has_content(source: Dict[str, Any]) -> bool:
        if not source:
            return False
        for key, value in source.items():
            if key in {"source", "_uncertain_fields"}:
                continue
            if MergeEngine._is_present(value):
                return True
        return False
