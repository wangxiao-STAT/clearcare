"""Load and query pre-generated service explanations."""

import json
from pathlib import Path

DEFAULT_PATH = Path(__file__).parent.parent / "data" / "processed" / "service_explanations.json"

REQUIRED_FIELDS = [
    "description",
    "typically_included",
    "billed_separately",
    "what_to_expect",
    "questions_to_ask",
]


def load_explanations(path: str | None = None) -> dict[str, dict]:
    """Load service explanations from JSON.

    Returns a dict mapping service_name to an explanation dict.
    Raises FileNotFoundError if the file is missing (fail loudly).
    """
    p = Path(path) if path else DEFAULT_PATH
    with p.open() as f:
        return json.load(f)


def get_explanation(explanations: dict, service_name: str) -> dict | None:
    """Return the explanation for a service, or None if not found."""
    return explanations.get(service_name)
