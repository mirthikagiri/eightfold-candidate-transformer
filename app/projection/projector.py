from typing import Any, Dict, List, Optional

from app.normalizers.email import normalize_email
from app.normalizers.phone import normalize_phone
from app.normalizers.skills import normalize_skills
from app.projection.models import ProjectionPlan, ProjectionResult


class ProjectionEngine:

    def _resolve_path(self, data: dict, path: Optional[str]) -> Any:
        """
        Supports:
        full_name
        emails[0]
        phones[0]
        location.city
        """
        if not path:
            return None

        if "[" in path and "]" in path:
            field = path.split("[")[0]
            index = int(path.split("[")[1].replace("]", ""))
            values = data.get(field, [])
            if isinstance(values, list) and len(values) > index:
                return values[index]
            return None

        if "." in path:
            current: Any = data
            for part in path.split("."):
                if not isinstance(current, dict):
                    return None
                current = current.get(part)
            return current

        return data.get(path)

    def _apply_normalizer(self, value: Any, normalizer: Optional[str]) -> Any:
        if value is None:
            return None

        if normalizer == "E164":
            return normalize_phone(value)

        if normalizer == "email":
            return normalize_email(value)

        if normalizer == "canonical":
            if isinstance(value, list):
                return normalize_skills(value)
            return value

        return value

    def _record_missing_event(
        self,
        missing_events: List[Dict[str, Any]],
        field_path: str,
        source_field: str,
        strategy: str,
        action: str,
    ) -> None:
        missing_events.append(
            {
                "field": field_path,
                "source_field": source_field,
                "strategy": strategy,
                "action": action,
                "reason": "missing",
            }
        )

    def project(
        self,
        canonical: dict,
        plan: ProjectionPlan,
    ) -> ProjectionResult:
        output: Dict[str, Any] = {}
        missing_events: List[Dict[str, Any]] = []

        for field in plan.fields:
            source_field = field.from_field if field.from_field else field.path
            value = self._resolve_path(canonical, field.from_field)

            if value is None:
                if plan.on_missing == "omit":
                    self._record_missing_event(
                        missing_events,
                        field.path,
                        source_field,
                        strategy="omit",
                        action="omitted",
                    )
                    continue

                if plan.on_missing == "null":
                    output[field.path] = None
                    self._record_missing_event(
                        missing_events,
                        field.path,
                        source_field,
                        strategy="null",
                        action="set_null",
                    )
                    continue

                if plan.on_missing == "error":
                    self._record_missing_event(
                        missing_events,
                        field.path,
                        source_field,
                        strategy="error",
                        action="validation_error",
                    )
                    continue

                output[field.path] = None
                self._record_missing_event(
                    missing_events,
                    field.path,
                    source_field,
                    strategy=plan.on_missing,
                    action="set_null",
                )
                continue

            value = self._apply_normalizer(value, field.normalize)
            output[field.path] = value

        if plan.include_confidence and "confidence" in canonical:
            output["_confidence"] = canonical["confidence"]

        if plan.include_provenance and "provenance" in canonical:
            output["_provenance"] = canonical["provenance"]

        if plan.include_quality and "quality_report" in canonical:
            output["_quality"] = canonical["quality_report"]

        if plan.include_audit and "_audit" in canonical:
            output["_audit"] = canonical["_audit"]

        if plan.include_conflicts and "conflict_report" in canonical:
            output["_conflicts"] = canonical["conflict_report"]

        if plan.include_normalization_report and "normalization_report" in canonical:
            output["_normalization_report"] = canonical["normalization_report"]

        return ProjectionResult(output=output, missing_events=missing_events)
