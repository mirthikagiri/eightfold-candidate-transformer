import json
from pathlib import Path
from typing import Any, Dict


class OutputGenerator:
    """Write pipeline results to JSON files on disk."""

    @staticmethod
    def write_projected(output_path: str, data: Dict[str, Any]) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=4)
        return path

    @staticmethod
    def write_canonical(canonical_path: str, data: Dict[str, Any]) -> Path:
        path = Path(canonical_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=4, default=str)
        return path
