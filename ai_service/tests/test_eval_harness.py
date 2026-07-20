"""Tests for the offline eval harness."""

import json
from pathlib import Path

import pytest


@pytest.fixture
def golden_path(tmp_path) -> Path:
    p = tmp_path / "golden.jsonl"
    p.write_text(
        "\n".join(
            [
                json.dumps({"raw": "a", "category": "contact"}),
                json.dumps({"raw": "b", "category": "invoice"}),
                json.dumps({"raw": "c", "category": "contact"}),
            ]
        )
    )
    return p


def test_eval_email_parse_perfect_predictions_yield_f1_1(golden_path):
    """Matching predictions give a macro F1 of 1.0."""
    from ai_service.eval.harness import eval_email_parse

    metrics = eval_email_parse(
        golden_path,
        [{"category": "contact"}, {"category": "invoice"}, {"category": "contact"}],
    )
    assert metrics["macro_f1"] == 1.0


def test_eval_email_parse_handles_mismatched_predictions(golden_path):
    """A single wrong prediction lowers macro F1 below 1."""
    from ai_service.eval.harness import eval_email_parse

    metrics = eval_email_parse(
        golden_path,
        [{"category": "contact"}, {"category": "contact"}, {"category": "contact"}],
    )
    assert 0.0 <= metrics["macro_f1"] < 1.0


def test_eval_email_parse_includes_per_class_report(golden_path):
    """The result includes a per-class sklearn report string."""
    from ai_service.eval.harness import eval_email_parse

    metrics = eval_email_parse(
        golden_path,
        [{"category": "contact"}, {"category": "invoice"}, {"category": "contact"}],
    )
    assert "contact" in metrics["per_class"]
    assert "invoice" in metrics["per_class"]


def test_eval_email_parse_uses_repo_golden_fixture():
    """The repo's checked-in golden fixture parses and scores."""
    from ai_service.eval.harness import eval_email_parse

    fixture = Path(__file__).parent.parent / "eval" / "golden" / "email_parse.jsonl"
    metrics = eval_email_parse(
        fixture,
        [
            {"category": "contact"},
            {"category": "invoice"},
            {"category": "support"},
            {"category": "unknown"},
        ],
    )
    assert metrics["macro_f1"] == 1.0
