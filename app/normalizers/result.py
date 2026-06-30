from typing import Any, Dict, List, Optional, Tuple


def make_normalization_entry(
    field: str,
    source: str,
    raw_value: Any,
    normalized_value: Any,
    status: str,
    reason: Optional[str] = None,
) -> Dict[str, Any]:
    entry: Dict[str, Any] = {
        "field": field,
        "source": source,
        "raw_value": raw_value,
        "normalized_value": normalized_value,
        "status": status,
    }
    if reason:
        entry["reason"] = reason
    return entry


class NormalizationReport:
    """Collect normalization outcomes without interrupting the pipeline."""

    def __init__(self) -> None:
        self._entries: List[Dict[str, Any]] = []

    def add(self, entry: Dict[str, Any]) -> None:
        self._entries.append(entry)

    def extend(self, entries: List[Dict[str, Any]]) -> "NormalizationReport":
        self._entries.extend(entries)
        return self

    @property
    def entries(self) -> List[Dict[str, Any]]:
        return list(self._entries)

    @property
    def failure_count(self) -> int:
        return sum(1 for entry in self._entries if entry.get("status") == "invalid")

    def to_list(self) -> List[Dict[str, Any]]:
        return self.entries

    @classmethod
    def merge(
        cls,
        *reports: Optional["NormalizationReport"],
    ) -> "NormalizationReport":
        combined = cls()
        for report in reports:
            if report:
                combined.extend(report.entries)
        return combined
