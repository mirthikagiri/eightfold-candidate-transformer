import json

from app.projection.models import FieldRule, ProjectionPlan


class ConfigCompiler:

    def compile(self, config_path: str) -> ProjectionPlan:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        fields = []
        for field in config["fields"]:
            fields.append(
                FieldRule(
                    path=field["path"],
                    from_field=field.get("from", field["path"]),
                    normalize=field.get("normalize"),
                    required=field.get("required", False),
                )
            )

        return ProjectionPlan(
            fields=fields,
            include_confidence=config.get("include_confidence", False),
            include_provenance=config.get("include_provenance", False),
            include_quality=config.get("include_quality", False),
            include_audit=config.get("include_audit", False),
            on_missing=config.get("on_missing", "null"),
        )
