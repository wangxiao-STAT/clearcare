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
