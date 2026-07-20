"""Tests for the Presidio-backed PII scrubber.

These tests mock the underlying Presidio engines so they run in CI
without requiring the spacy model to be reloaded on every invocation.
"""

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_presidio():
    """Patch the module-level Presidio engine instances."""
    fake_analyzer = MagicMock()
    fake_anonymizer = MagicMock()
    fake_analyzer.analyze.return_value = []
    anonymized = MagicMock()
    anonymized.text = "REDACTED"
    fake_anonymizer.anonymize.return_value = anonymized
    with patch("ai_service.safety.pii._analyzer", fake_analyzer), patch(
        "ai_service.safety.pii._anonymizer", fake_anonymizer
    ):
        yield fake_analyzer, fake_anonymizer


def test_redact_pii_returns_anonymized_text(mock_presidio):
    """``redact_pii`` runs analyze + anonymize and returns the new text."""
    fake_analyzer, fake_anonymizer = mock_presidio
    fake_analyzer.analyze.return_value = [MagicMock(entity_type="EMAIL_ADDRESS")]
    out = __import__("ai_service.safety.pii", fromlist=["redact_pii"]).redact_pii(
        "contact alice@example.com"
    )
    assert out == "REDACTED"
    fake_analyzer.analyze.assert_called_once()
    fake_anonymizer.anonymize.assert_called_once()


def test_contains_pii_true_when_entities_found(mock_presidio):
    """``contains_pii`` returns True when the analyzer yields any result."""
    fake_analyzer, _ = mock_presidio
    fake_analyzer.analyze.return_value = [MagicMock(entity_type="PHONE_NUMBER")]
    pii = __import__("ai_service.safety.pii", fromlist=["contains_pii"])
    assert pii.contains_pii("call 555-1234") is True


def test_contains_pii_false_when_no_entities(mock_presidio):
    """``contains_pii`` returns False on a clean string."""
    fake_analyzer, _ = mock_presidio
    fake_analyzer.analyze.return_value = []
    pii = __import__("ai_service.safety.pii", fromlist=["contains_pii"])
    assert pii.contains_pii("hello world") is False


@pytest.mark.parametrize(
    "text, expected_entity",
    [
        ("Email me at jane@x.io", "EMAIL_ADDRESS"),
        ("Call 415-555-1234", "PHONE_NUMBER"),
    ],
)
def test_presidio_engine_smoke(text, expected_entity):
    """The real Presidio engine (no mocks) detects the listed entities.

    This is a live smoke test; it requires the spacy ``en_core_web_lg``
    model to be available. The model is auto-downloaded on first import.
    """
    from presidio_analyzer import AnalyzerEngine

    results = AnalyzerEngine().analyze(text=text, language="en")
    types = {r.entity_type for r in results}
    assert expected_entity in types
