from typing import Any, Dict, List, Optional, Tuple

from app.merger.conflict_resolver import ConflictResolver
from app.normalizers.email import normalize_email_detailed
from app.normalizers.location import location_to_string, normalize_location
from app.normalizers.phone import normalize_phone_detailed
from app.normalizers.skills import normalize_skills


class MergeEngine:
    """
    Deterministic merge of candidate data from multiple sources into
    a canonical candidate record with conflict tracking.
    """

    RESUME_SOURCE = "resume_pdf"
    CSV_SOURCE = "recruiter_csv"

    def __init__(self) -> None:
        self._conflict_resolver = ConflictResolver()

    def merge(
        self,
        csv_data: Dict[str, Any],
        resume_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        conflict_report: List[Dict[str, Any]] = []
        merge_decisions: Dict[str, Dict[str, Any]] = {}

        canonical: Dict[str, Any] = {}

        canonical["full_name"], decision = self._merge_scalar(
            "full_name",
            csv_data.get("full_name"),
            resume_data.get("full_name"),
            prefer=self.RESUME_SOURCE,
            policy=ConflictResolver.REASON_RESUME_PRIORITY,
        )
        merge_decisions["full_name"] = decision
        self._record_conflict(conflict_report, decision)

        canonical["headline"], decision = self._merge_scalar(
            "headline",
            csv_data.get("headline"),
            resume_data.get("headline"),
            prefer=self.RESUME_SOURCE,
            policy=ConflictResolver.REASON_RESUME_PRIORITY,
        )
        merge_decisions["headline"] = decision
        self._record_conflict(conflict_report, decision)

        canonical["years_experience"], decision = self._merge_scalar(
            "years_experience",
            csv_data.get("years_experience"),
            resume_data.get("years_experience"),
            prefer=self.RESUME_SOURCE,
            policy=ConflictResolver.REASON_RESUME_PRIORITY,
        )
        merge_decisions["years_experience"] = decision
        self._record_conflict(conflict_report, decision)

        canonical["location"], decision = self._merge_location(
            csv_data.get("location"),
            resume_data.get("location"),
        )
        merge_decisions["location"] = decision
        self._record_conflict(conflict_report, decision)

        canonical["emails"], decision = self._merge_emails(
            csv_data.get("emails", []),
            resume_data.get("emails", []),
        )
        merge_decisions["emails"] = decision
        self._record_conflict(conflict_report, decision)

        canonical["phones"], decision = self._merge_phones(
            csv_data.get("phones", []),
            resume_data.get("phones", []),
        )
        merge_decisions["phones"] = decision
        self._record_conflict(conflict_report, decision)

        canonical["skills"] = normalize_skills(
            list(
                set(
                    (csv_data.get("skills") or [])
                    + (resume_data.get("skills") or [])
                )
            )
        )
        merge_decisions["skills"] = {
            "selected": canonical["skills"],
            "selected_source": None,
            "candidate_values": [],
            "resolution_policy": "union_canonical",
            "sources": self._list_sources(
                csv_data.get("skills", []),
                resume_data.get("skills", []),
            ),
            "conflict": None,
        }

        canonical["links"] = self._merge_links(
            csv_data.get("links", []),
            resume_data.get("links", []),
        )
        merge_decisions["links"] = {
            "selected": canonical["links"],
            "selected_source": None,
            "candidate_values": [],
            "resolution_policy": "union_dedupe",
            "sources": self._list_sources(
                csv_data.get("links", []),
                resume_data.get("links", []),
            ),
            "conflict": None,
        }

        canonical["experience"] = self._merge_unique_entries(
            csv_data.get("experience", []),
            resume_data.get("experience", []),
        )
        merge_decisions["experience"] = {
            "selected": canonical["experience"],
            "selected_source": None,
            "candidate_values": [],
            "resolution_policy": "merge_unique",
            "sources": self._list_sources(
                csv_data.get("experience", []),
                resume_data.get("experience", []),
            ),
            "conflict": None,
        }

        canonical["education"] = self._merge_unique_entries(
            csv_data.get("education", []),
            resume_data.get("education", []),
        )
        merge_decisions["education"] = {
            "selected": canonical["education"],
            "selected_source": None,
            "candidate_values": [],
            "resolution_policy": "merge_unique",
            "sources": self._list_sources(
                csv_data.get("education", []),
                resume_data.get("education", []),
            ),
            "conflict": None,
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
        field: str,
        csv_value: Any,
        resume_value: Any,
        prefer: str,
        policy: str,
    ) -> Tuple[Any, Dict[str, Any]]:
        csv_present = self._is_present(csv_value)
        resume_present = self._is_present(resume_value)

        decision = self._conflict_resolver.resolve_scalar(
            field=field,
            csv_value=csv_value if csv_present else None,
            resume_value=resume_value if resume_present else None,
            csv_source=self.CSV_SOURCE,
            resume_source=self.RESUME_SOURCE,
            prefer=prefer,
            policy=policy,
        )

        return decision["selected"], {
            "selected": decision["selected"],
            "selected_source": decision["selected_source"],
            "candidate_values": decision["candidate_values"],
            "competing_values": [
                candidate["value"] for candidate in decision["candidate_values"]
            ],
            "resolution_policy": decision["resolution_policy"],
            "sources": [
                candidate["source"] for candidate in decision["candidate_values"]
            ],
            "conflict": decision["conflict"],
        }

    def _merge_location(
        self,
        csv_value: Any,
        resume_value: Any,
    ) -> Tuple[Optional[Dict[str, Optional[str]]], Dict[str, Any]]:
        csv_location = normalize_location(csv_value)
        resume_location = normalize_location(resume_value)

        csv_display = location_to_string(csv_location) if csv_location else None
        resume_display = (
            location_to_string(resume_location) if resume_location else None
        )

        decision = self._conflict_resolver.resolve_scalar(
            field="location",
            csv_value=csv_display,
            resume_value=resume_display,
            csv_source=self.CSV_SOURCE,
            resume_source=self.RESUME_SOURCE,
            prefer=self.RESUME_SOURCE,
            policy=ConflictResolver.REASON_HIGHEST_CONFIDENCE,
            csv_status="valid" if csv_location else "invalid",
            resume_status="valid" if resume_location else "invalid",
        )

        selected = resume_location if resume_location else csv_location

        return selected, {
            "selected": location_to_string(selected) if selected else None,
            "selected_source": decision["selected_source"],
            "candidate_values": decision["candidate_values"],
            "competing_values": [
                candidate["value"]
                for candidate in decision["candidate_values"]
                if candidate.get("value")
            ],
            "resolution_policy": decision["resolution_policy"],
            "sources": [
                candidate["source"] for candidate in decision["candidate_values"]
            ],
            "display": location_to_string(selected) if selected else None,
            "conflict": decision["conflict"],
        }

    def _merge_emails(
        self,
        csv_emails: List[str],
        resume_emails: List[str],
    ) -> Tuple[List[str], Dict[str, Any]]:
        csv_items = self._email_candidates(csv_emails, self.CSV_SOURCE)
        resume_items = self._email_candidates(resume_emails, self.RESUME_SOURCE)

        decision = self._conflict_resolver.resolve_collection(
            field="emails",
            csv_items=csv_items,
            resume_items=resume_items,
            dedupe_key="value",
            policy="union_dedupe",
        )

        return decision["selected"], {
            "selected": decision["selected"],
            "selected_source": decision["selected_source"],
            "candidate_values": decision["candidate_values"],
            "competing_values": [],
            "resolution_policy": decision["resolution_policy"],
            "sources": decision["sources"],
            "conflict": decision["conflict"],
        }

    def _merge_phones(
        self,
        csv_phones: List[str],
        resume_phones: List[str],
    ) -> Tuple[List[str], Dict[str, Any]]:
        csv_items = self._phone_candidates(csv_phones, self.CSV_SOURCE)
        resume_items = self._phone_candidates(resume_phones, self.RESUME_SOURCE)

        decision = self._conflict_resolver.resolve_collection(
            field="phones",
            csv_items=csv_items,
            resume_items=resume_items,
            dedupe_key="value",
            policy="union_dedupe",
        )

        return decision["selected"], {
            "selected": decision["selected"],
            "selected_source": decision["selected_source"],
            "candidate_values": decision["candidate_values"],
            "competing_values": [],
            "resolution_policy": decision["resolution_policy"],
            "sources": decision["sources"],
            "conflict": decision["conflict"],
        }

    def _phone_candidates(
        self,
        phones: List[str],
        source: str,
    ) -> List[Dict[str, Any]]:
        candidates = []
        for phone in phones:
            if not phone:
                continue
            normalized, status, _reason = normalize_phone_detailed(phone)
            candidates.append(
                {
                    "source": source,
                    "value": normalized,
                    "raw_value": phone,
                    "status": status,
                }
            )
        return candidates

    def _email_candidates(
        self,
        emails: List[str],
        source: str,
    ) -> List[Dict[str, Any]]:
        candidates = []
        for email in emails:
            if not email:
                continue
            normalized, status, _reason = normalize_email_detailed(email)
            candidates.append(
                {
                    "source": source,
                    "value": normalized,
                    "raw_value": email,
                    "status": status,
                }
            )
        return candidates

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

    def _record_conflict(
        self,
        conflict_report: List[Dict[str, Any]],
        decision: Dict[str, Any],
    ) -> None:
        conflict = decision.get("conflict")
        if conflict:
            conflict_report.append(conflict)

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
            if key in {"source", "_uncertain_fields", "_normalization_report"}:
                continue
            if MergeEngine._is_present(value):
                return True
        return False
