import json
import tempfile
from pathlib import Path

from app.output.generator import OutputGenerator


def test_write_projected_creates_json_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = str(Path(tmpdir) / "out" / "profile.json")
        data = {"candidate_name": "Jane Doe"}

        written = OutputGenerator.write_projected(path, data)

        assert written.exists()
        with open(written, encoding="utf-8") as handle:
            assert json.load(handle) == data


def test_write_canonical_creates_json_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = str(Path(tmpdir) / "canonical.json")
        data = {"full_name": "Jane Doe", "candidate_id": "cand_abc123"}

        written = OutputGenerator.write_canonical(path, data)

        assert written.exists()
        with open(written, encoding="utf-8") as handle:
            assert json.load(handle)["full_name"] == "Jane Doe"
