from typing import Any, Dict, List

from app.projection.models import ProjectionPlan


class ProjectionValidator:

    def validate(
        self,
        output: Dict[str, Any],
        plan: ProjectionPlan,
        missing_events: List[Dict[str, Any]] | None = None,
    ) -> Dict[str, Any]:
        missing_events = missing_events or []
        errors: List[Dict[str, Any]] = []
        warnings: List[Dict[str, Any]] = []
        missing_decisions: List[Dict[str, Any]] = []
        error_fields = set()

        for event in missing_events:
            missing_decisions.append(
                {
                    "field": event["field"],
                    "strategy": event["strategy"],
                    "action": event["action"],
                }
            )

            if event["action"] == "validation_error":
                errors.append(
                    {
                        "field": event["field"],
                        "severity": "error",
                        "message": "Required field missing",
                    }
                )
                error_fields.add(event["field"])
            elif event["action"] == "omitted":
                warnings.append(
                    {
                        "field": event["field"],
                        "strategy": "omit",
                        "action": "omitted",
                        "message": f"{event['field']} missing",
                    }
                )

        for field in plan.fields:
            value = output.get(field.path)
            field_present = field.path in output

            if field.required and (not field_present or value is None):
                if field.path in error_fields:
                    continue
                errors.append(
                    {
                        "field": field.path,
                        "severity": "error",
                        "message": f"{field.path} is required",
                    }
                )
                continue

            if value is None and not field.required:
                if any(warning["field"] == field.path for warning in warnings):
                    continue
                if field_present or plan.on_missing != "omit":
                    warnings.append(
                        {
                            "field": field.path,
                            "strategy": plan.on_missing,
                            "action": "set_null" if field_present else "missing",
                            "message": f"{field.path} is missing",
                        }
                    )

            if (
                field.normalize == "E164"
                and value is None
                and field.from_field
                and field_present
            ):
                warnings.append(
                    {
                        "field": field.path,
                        "strategy": plan.on_missing,
                        "action": "normalization_failed",
                        "message": f"{field.path} could not be normalized to E.164",
                    }
                )

            if (
                not field.required
                and not field_present
                and plan.on_missing == "omit"
                and not any(w["field"] == field.path for w in warnings)
            ):
                warnings.append(
                    {
                        "field": field.path,
                        "strategy": "omit",
                        "action": "omitted",
                        "message": f"{field.path} is missing",
                    }
                )

        passed = len(errors) == 0

        return {
            "validation": {
                "passed": passed,
                "errors": errors,
                "warnings": warnings,
                "missing_decisions": missing_decisions,
            }
        }
