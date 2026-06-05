"""Test configuration and shared fixtures."""
import pytest
import json
import os
import sys

# Ensure the backend package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.rules.adjudication_engine import AdjudicationEngine
from app.rules.policy_loader import PolicyTerms, get_policy


@pytest.fixture(scope="module")
def engine():
    """Return a fresh adjudication engine instance."""
    return AdjudicationEngine()


@pytest.fixture(scope="module")
def policy():
    """Return loaded policy terms."""
    return get_policy()


@pytest.fixture(scope="module")
def test_cases():
    """Load test_cases.json."""
    path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "..", "test_cases.json"
    )
    # Normalize path
    path = os.path.abspath(path)
    if not os.path.exists(path):
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "test_cases.json")
    with open(path, "r") as f:
        return json.load(f)["test_cases"]
