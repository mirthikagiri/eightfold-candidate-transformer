from typing import Any, Dict, List

from app.projection.models import ProjectionPlan


class ProjectionValidator:

    def validate(
        self,
        output: Dict[str, Any],
        plan: ProjectionPlan,
    ) -> Dict[str, List[str]]:
        errors: List[str] = []
        warnings: List[str] = []

        for field in plan.fields:
            value = output.get(field.path)

            if field.required and value is None:
                errors.append(f"{field.path} is required")

            if value is None and not field.required:
                warnings.append(f"{field.path} is missing")

            if field.normalize == "E164" and value is None and field.from_field:
                warnings.append(
                    f"{field.path} could not be normalized to E.164"
                )

        return {
            "errors": errors,
            "warnings": warnings,
        }
