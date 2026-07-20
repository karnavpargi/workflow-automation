"""Tests for the ``MAKE_REAL=1`` eval runner.

We use a mocked chat model to verify the runner invokes the agent
for each golden row and feeds the resulting predictions into
``eval_email_parse``. The synthetic path is also covered (it is the
default when ``MAKE_REAL`` is unset).
"""

from unittest.mock import MagicMock, patch


def _golden_rows():
    """Return the in-repo golden set as a list of dicts."""
    from pathlib import Path

    from ai_service.eval.harness import load_golden

    p = (
        Path(__file__).resolve().parent.parent.parent
        / "ai_service"
        / "eval"
        / "golden"
        / "email_parse.jsonl"
    )
    df = load_golden(p)
    return df.to_dict(orient="records")


def test_collect_predictions_returns_synthetic_by_default(monkeypatch):
    """Without ``MAKE_REAL=1`` the runner uses the synthetic vector."""
    from ops.eval import run_nightly

    monkeypatch.delenv("MAKE_REAL", raising=False)
    preds = run_nightly.collect_predictions()
    assert preds == _synthetic_predictions_for_golden()


def _synthetic_predictions_for_golden() -> list[dict]:
    """Hard-coded perfect predictions matching the golden set in order."""
    return [
        {"category": "contact"},
        {"category": "invoice"},
        {"category": "support"},
        {"category": "unknown"},
    ]


def test_collect_predictions_invokes_agent_when_make_real(monkeypatch):
    """With ``MAKE_REAL=1``, the runner builds the graph and calls it per row."""
    from ops.eval import run_nightly

    monkeypatch.setenv("MAKE_REAL", "1")
    rows = _golden_rows()
    # Each invocation returns a result with a specific category
    expected = ["contact", "invoice", "support", "unknown"]

    with patch("ai_service.agents.email_parse.build_email_parse_graph") as build:
        graph = MagicMock()
        build.return_value = graph
        graph.invoke.side_effect = [{"result": {"category": cat}} for cat in expected]
        preds = run_nightly.collect_predictions()
    assert len(preds) == len(rows)
    assert [p["category"] for p in preds] == expected


def test_collect_predictions_falls_back_to_unknown_on_agent_error(monkeypatch):
    """A failing agent row falls back to ``category=unknown``."""
    from ops.eval import run_nightly

    monkeypatch.setenv("MAKE_REAL", "1")
    with patch("ai_service.agents.email_parse.build_email_parse_graph") as build:
        graph = MagicMock()
        build.return_value = graph
        graph.invoke.side_effect = RuntimeError("LLM down")
        preds = run_nightly.collect_predictions()
    assert all(p == {"category": "unknown"} for p in preds)
    assert len(preds) == 4
