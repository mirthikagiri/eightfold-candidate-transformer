import json
from typing import Any, Dict, Union

from app.projection.config_validator import ConfigValidationError, ConfigValidator
from app.projection.models import FieldRule, ProjectionPlan


class ConfigCompiler:

    def compile(self, config_path: str) -> ProjectionPlan:
        config = self._load_config(config_path)
        validation = ConfigValidator().validate(config)
        if not validation["valid"]:
            raise ConfigValidationError(validation["errors"])

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
            include_conflicts=config.get("include_conflicts", False),
            include_normalization_report=config.get(
                "include_normalization_report",
                False,
            ),
            include_validation=config.get("include_validation", False),
            on_missing=config.get("on_missing", "null"),
            identity_warning_threshold=float(
                config.get("identity_warning_threshold", 0.50)
            ),
        )

    def validate_file(self, config_path: str) -> Dict[str, Union[bool, list]]:
        try:
            config = self._load_config(config_path)
        except ConfigValidationError as exc:
            return {"valid": False, "errors": exc.errors}

        return ConfigValidator().validate(config)

    @staticmethod
    def _load_config(config_path: str) -> Dict[str, Any]:
        try:
            with open(config_path, "r", encoding="utf-8") as handle:
                config = json.load(handle)
        except json.JSONDecodeError as exc:
            raise ConfigValidationError([f"Invalid JSON in config file: {exc.msg}"]) from exc
        except OSError as exc:
            raise ConfigValidationError([f"Unable to read config file: {exc}"]) from exc

        if not isinstance(config, dict):
            raise ConfigValidationError(["Config root must be a JSON object"])

        return config
