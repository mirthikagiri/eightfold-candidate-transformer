from app.normalizers.skills import normalize_skills
from app.normalizers.phone import normalize_phone

from app.projection.models import (
    ProjectionPlan
)


class ProjectionEngine:

    def _resolve_path(self, data, path):
        """
    Supports:
    full_name
    emails[0]
    phones[0]
    """ 
        if not path:
            return None

        if "[" in path and "]" in path:

            field = path.split("[")[0]

            index = int(
            path.split("[")[1]
            .replace("]", "")
        )

            values = data.get(field, [])

            if (
            isinstance(values, list)
            and len(values) > index
        ):
                return values[index]

            return None

        return data.get(path)
    def _apply_normalizer(self, value, normalizer):
        if value is None:
            return None
        if normalizer=="E164":
            return normalize_phone(value)
        if normalizer=="canonical":
            if isinstance(value, list):
                return normalize_skills(value)
            return value
        return value
    def project(
        self,
        canonical,
        plan: ProjectionPlan
    ):

        output = {}

        for field in plan.fields:

            source_field = (field.from_field if field.from_field else field.path)

            value = self._resolve_path(
                canonical,
                field.from_field
            )

            if value is None:

                if plan.on_missing == "omit":
                    continue

                if plan.on_missing == "null":
                    output[field.path] = None
                    continue

                if plan.on_missing == "error":
                    raise ValueError(
                        f"Missing field: {source_field}"
                    )

            value=self._apply_normalizer(
                value,
                field.normalize)
            output[field.path] = value

        if (
            plan.include_confidence
            and "confidence" in canonical
        ):
            output["_confidence"] = (
                canonical["confidence"]
            )

        if (
            plan.include_provenance
            and "provenance" in canonical
        ):
            output["_provenance"] = (
                canonical["provenance"]
            )

        return output