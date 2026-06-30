from typing import Any, Dict, List, Optional


class ConflictResolver:
    """
    Resolve competing field values with explicit, explainable policies.
    """

    REASON_RESUME_PRIORITY = "resume_priority"
    REASON_SOURCE_AGREEMENT = "source_agreement"
    REASON_VALID_VALUE_PRIORITY = "valid_value_priority"
    REASON_HIGHEST_CONFIDENCE = "highest_confidence"
    REASON_MOST_COMPLETE_VALUE = "most_complete_value"

    def resolve_scalar(
        self,
        field: str,
        csv_value: Any,
        resume_value: Any,
        csv_source: str,
        resume_source: str,
        prefer: str,
        policy: str,
        csv_status: str = "valid",
        resume_status: str = "valid",
    ) -> Dict[str, Any]:
        candidates = self._build_candidates(
            csv_value,
            resume_value,
            csv_source,
            resume_source,
            csv_status,
            resume_status,
        )
        present = [candidate for candidate in candidates if candidate["value"] is not None]

        if not present:
            return self._empty_decision(field, policy)

        if len(present) == 1:
            selected = present[0]
            return {
                "field": field,
                "selected": selected["value"],
                "selected_source": selected["source"],
                "candidate_values": candidates,
                "resolution_policy": self.REASON_SOURCE_AGREEMENT,
                "conflict": None,
            }

        valid = [candidate for candidate in present if candidate["status"] == "valid"]
        invalid = [candidate for candidate in present if candidate["status"] == "invalid"]

        if valid and invalid:
            selected = self._select_by_preference(valid, prefer, resume_source)
            return {
                "field": field,
                "selected": selected["value"],
                "selected_source": selected["source"],
                "candidate_values": candidates,
                "resolution_policy": self.REASON_VALID_VALUE_PRIORITY,
                "conflict": self._build_conflict(
                    field,
                    candidates,
                    selected["value"],
                    self.REASON_VALID_VALUE_PRIORITY,
                ),
            }

        unique_values = self._unique_values(present)
        if len(unique_values) == 1:
            selected = present[0]
            return {
                "field": field,
                "selected": selected["value"],
                "selected_source": selected["source"],
                "candidate_values": candidates,
                "resolution_policy": self.REASON_SOURCE_AGREEMENT,
                "conflict": None,
            }

        if prefer == resume_source:
            selected = self._select_by_preference(valid or present, prefer, resume_source)
            reason = policy if policy else self.REASON_RESUME_PRIORITY
        else:
            selected = self._select_by_preference(valid or present, prefer, resume_source)
            reason = policy

        return {
            "field": field,
            "selected": selected["value"],
            "selected_source": selected["source"],
            "candidate_values": candidates,
            "resolution_policy": reason,
            "conflict": self._build_conflict(
                field,
                candidates,
                selected["value"],
                reason,
            ),
        }

    def resolve_collection(
        self,
        field: str,
        csv_items: List[Dict[str, Any]],
        resume_items: List[Dict[str, Any]],
        dedupe_key: str = "value",
        policy: str = "union_dedupe",
    ) -> Dict[str, Any]:
        candidates = csv_items + resume_items
        valid_items = [item for item in candidates if item.get("status") == "valid"]
        invalid_items = [item for item in candidates if item.get("status") == "invalid"]

        merged: Dict[str, Any] = {}
        for item in valid_items:
            key = item.get(dedupe_key)
            if key:
                merged[key] = item

        selected_values = sorted(
            item.get("value") for item in merged.values() if item.get("value")
        )

        conflict = None
        resolution_policy = policy

        if invalid_items and valid_items:
            resolution_policy = self.REASON_VALID_VALUE_PRIORITY
            conflict = self._build_conflict(
                field,
                candidates,
                selected_values,
                self.REASON_VALID_VALUE_PRIORITY,
            )
        elif len({item.get("value") for item in valid_items}) > 1:
            distinct = self._unique_values(valid_items)
            if len(distinct) > 1:
                conflict = self._build_conflict(
                    field,
                    candidates,
                    selected_values,
                    policy,
                )

        sources = sorted(
            {
                item.get("source")
                for item in candidates
                if item.get("source") and item.get("value") is not None
            }
        )

        return {
            "field": field,
            "selected": selected_values,
            "selected_source": sources[0] if len(sources) == 1 else None,
            "candidate_values": candidates,
            "resolution_policy": resolution_policy,
            "sources": sources,
            "conflict": conflict,
        }

    def _build_candidates(
        self,
        csv_value: Any,
        resume_value: Any,
        csv_source: str,
        resume_source: str,
        csv_status: str,
        resume_status: str,
    ) -> List[Dict[str, Any]]:
        candidates = []
        if csv_value is not None and csv_value != "":
            candidates.append(
                {
                    "source": csv_source,
                    "value": csv_value,
                    "status": csv_status,
                }
            )
        if resume_value is not None and resume_value != "":
            candidates.append(
                {
                    "source": resume_source,
                    "value": resume_value,
                    "status": resume_status,
                }
            )
        return candidates

    @staticmethod
    def _select_by_preference(
        candidates: List[Dict[str, Any]],
        prefer: str,
        resume_source: str,
    ) -> Dict[str, Any]:
        for candidate in candidates:
            if candidate.get("source") == prefer:
                return candidate
        return candidates[0]

    @staticmethod
    def _unique_values(candidates: List[Dict[str, Any]]) -> List[Any]:
        seen = []
        for candidate in candidates:
            value = candidate.get("value")
            normalized = str(value).strip().lower() if value is not None else None
            if normalized not in {str(item).strip().lower() for item in seen}:
                seen.append(value)
        return seen

    @staticmethod
    def _build_conflict(
        field: str,
        candidates: List[Dict[str, Any]],
        selected: Any,
        reason: str,
    ) -> Dict[str, Any]:
        return {
            "field": field,
            "values": [
                {
                    "source": candidate.get("source"),
                    "value": candidate.get("value"),
                    "status": candidate.get("status", "valid"),
                }
                for candidate in candidates
                if candidate.get("value") is not None
            ],
            "selected": selected,
            "reason": reason,
        }

    @staticmethod
    def _empty_decision(field: str, policy: str) -> Dict[str, Any]:
        return {
            "field": field,
            "selected": None,
            "selected_source": None,
            "candidate_values": [],
            "resolution_policy": policy,
            "conflict": None,
        }
