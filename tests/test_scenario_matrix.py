import json
import re
from pathlib import Path


ROOT = Path(__file__).parents[1]


def _spec_scenarios() -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for path in sorted((ROOT / "openspec" / "changes" / "backend-core-audit" / "specs").glob("*/spec.md")):
        result[path.parent.name] = re.findall(r"^#### Scenario: (.+)$", path.read_text(encoding="utf-8"), re.MULTILINE)
    return result


def test_backend_scenario_matrix_maps_every_active_spec_scenario_exactly():
    matrix = json.loads((ROOT / "data" / "validation" / "scenario-matrix-v1.json").read_text(encoding="utf-8"))
    assert matrix["schema_version"] == "scenario-matrix-v1"
    expected = _spec_scenarios()
    assert set(matrix["capabilities"]) == set(expected)
    for capability, scenarios in expected.items():
        entry = matrix["capabilities"][capability]
        assert entry["scenarios"] == scenarios
        assert entry["evidence"]
        assert len(entry["evidence"]) == len(set(entry["evidence"]))
        assert all(isinstance(value, str) and value.strip() for value in entry.get("blocked", []))


def test_scenario_matrix_never_represents_blocked_acceptance_as_passing():
    matrix = json.loads((ROOT / "data" / "validation" / "scenario-matrix-v1.json").read_text(encoding="utf-8"))
    blocked = {name for name, entry in matrix["capabilities"].items() if entry.get("blocked")}
    assert blocked == {"assessment-validation", "c-analysis", "isolated-execution", "java-analysis", "test-execution-agent"}
    text = (ROOT / "docs" / "backend" / "SCENARIO_MATRIX.md").read_text(encoding="utf-8")
    assert "Blocked rows are not counted as passing" in text
