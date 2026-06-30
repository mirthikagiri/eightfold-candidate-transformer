from typing import Any, Dict, List, Optional, Union


class ConfigValidationError(Exception):
    """Raised when projection config fails validation."""

    def __init__(self, errors: List[str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors))


class ConfigValidator:
    VALID_ON_MISSING = {"null", "omit", "error"}
    VALID_NORMALIZERS = {"email", "E164", "canonical"}
    INCLUDE_FLAGS = (
        "include_confidence",
        "include_provenance",
        "include_quality",
        "include_audit",
        "include_conflicts",
        "include_normalization_report",
        "include_validation",
    )

    def validate(self, config: Dict[str, Any]) -> Dict[str, Union[bool, List[str]]]:
        errors: List[str] = []

        if not isinstance(config, dict):
            errors.append("Config root must be a JSON object")
            return {"valid": False, "errors": errors}

        if "fields" not in config:
            errors.append("Config missing required key: fields")
        elif not isinstance(config["fields"], list):
            errors.append("Config field 'fields' must be a list")
        elif len(config["fields"]) == 0:
            errors.append("Config field 'fields' must not be empty")
        else:
            self._validate_fields(config["fields"], errors)

        on_missing = config.get("on_missing", "null")
        if on_missing not in self.VALID_ON_MISSING:
            errors.append(
                f"Invalid on_missing value: {on_missing!r}. "
                f"Must be one of: {', '.join(sorted(self.VALID_ON_MISSING))}"
            )

        for flag in self.INCLUDE_FLAGS:
            if flag in config and not isinstance(config[flag], bool):
                errors.append(f"Config field '{flag}' must be a boolean")

        threshold = config.get("identity_warning_threshold")
        if threshold is not None:
            if not isinstance(threshold, (int, float)):
                errors.append("Config field 'identity_warning_threshold' must be a number")
            elif not 0.0 <= float(threshold) <= 1.0:
                errors.append(
                    "Config field 'identity_warning_threshold' must be between 0.0 and 1.0"
                )

        return {"valid": len(errors) == 0, "errors": errors}

    def _validate_fields(self, fields: List[Any], errors: List[str]) -> None:
        paths_seen = set()
        for index, field in enumerate(fields):
            prefix = f"fields[{index}]"

            if not isinstance(field, dict):
                errors.append(f"{prefix} must be an object")
                continue

            path = field.get("path")
            if not path or not isinstance(path, str):
                errors.append(f"{prefix} missing required property: path")
            elif path in paths_seen:
                errors.append(f"{prefix} duplicate path: {path}")
            else:
                paths_seen.add(path)

            from_field = field.get("from", path)
            if from_field is not None and not isinstance(from_field, str):
                errors.append(f"{prefix}.from must be a string")

            normalize = field.get("normalize")
            if normalize is not None and normalize not in self.VALID_NORMALIZERS:
                errors.append(
                    f"{prefix} invalid normalize value: {normalize!r}. "
                    f"Must be one of: {', '.join(sorted(self.VALID_NORMALIZERS))}"
                )

            if "required" in field and not isinstance(field["required"], bool):
                errors.append(f"{prefix}.required must be a boolean")
