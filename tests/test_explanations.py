import json
import tempfile
import os
import pytest
from app.explanations import load_explanations, get_explanation, REQUIRED_FIELDS


def _make_test_explanations():
    return {
        "MRI Knee": {
            "description": "Test description.",
            "typically_included": ["a", "b"],
            "billed_separately": ["c", "d"],
            "what_to_expect": "Test expectations.",
            "questions_to_ask": ["q1", "q2"],
        }
    }


def test_load_explanations_returns_dict():
    data = _make_test_explanations()
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
        json.dump(data, f)
        path = f.name
    try:
        result = load_explanations(path)
    finally:
        os.unlink(path)
    assert isinstance(result, dict)
    assert "MRI Knee" in result
    assert result["MRI Knee"]["description"] == "Test description."


def test_load_explanations_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        load_explanations("/nonexistent/path/to/explanations.json")


def test_get_explanation_found():
    data = _make_test_explanations()
    result = get_explanation(data, "MRI Knee")
    assert result is not None
    assert result["description"] == "Test description."


def test_get_explanation_not_found():
    data = _make_test_explanations()
    result = get_explanation(data, "Unknown Service")
    assert result is None


def test_committed_json_has_all_services_with_required_fields():
    """Verify the real committed JSON has an entry for every service in SERVICE_CATALOG."""
    from pathlib import Path
    from app.search import SERVICE_CATALOG

    json_path = Path(__file__).parent.parent / "data" / "processed" / "service_explanations.json"
    if not json_path.exists():
        pytest.skip("service_explanations.json not yet generated")

    explanations = load_explanations(str(json_path))

    missing = []
    for svc in SERVICE_CATALOG:
        name = svc["name"]
        if name not in explanations:
            missing.append(name)
            continue
        entry = explanations[name]
        for field in REQUIRED_FIELDS:
            assert field in entry, f"{name} missing field '{field}'"
        assert isinstance(entry["description"], str), f"{name} description not a string"
        assert isinstance(entry["what_to_expect"], str), f"{name} what_to_expect not a string"
        assert isinstance(entry["typically_included"], list), f"{name} typically_included not a list"
        assert isinstance(entry["billed_separately"], list), f"{name} billed_separately not a list"
        assert isinstance(entry["questions_to_ask"], list), f"{name} questions_to_ask not a list"
        for item in entry["typically_included"]:
            assert isinstance(item, str), f"{name} has non-string in typically_included"
        for item in entry["billed_separately"]:
            assert isinstance(item, str), f"{name} has non-string in billed_separately"
        for item in entry["questions_to_ask"]:
            assert isinstance(item, str), f"{name} has non-string in questions_to_ask"

    assert not missing, f"Missing explanation entries for: {missing}"
