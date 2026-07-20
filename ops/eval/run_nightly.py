"""Run the golden-set eval and enforce the configured thresholds.

Two modes:

* Default (synthetic): uses a hard-coded perfect prediction vector. This
  path runs in CI without a live LLM and locks in the contract.
* ``MAKE_REAL=1``: iterates the golden set, invokes the email-parse
  agent for each ``raw`` field, and collects real predictions. This
  path requires the full stack (Ollama or OpenAI) and is the production
  nightly run.

Both modes feed :func:`ai_service.eval.harness.eval_email_parse` and
enforce ``thresholds.yaml``.

Usage:
    python ops/eval/run_nightly.py            # synthetic
    MAKE_REAL=1 python ops/eval/run_nightly.py # real
"""

import json
import os
from pathlib import Path

import yaml

from ai_service.eval.harness import eval_email_parse

THRESHOLDS_PATH = Path(__file__).parent / "thresholds.yaml"
GOLDEN_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "ai_service"
    / "eval"
    / "golden"
    / "email_parse.jsonl"
)
LAST_OK_MARKER = Path(__file__).parent / "last_ok"


def _synthetic_predictions() -> list[dict]:
    """Hard-coded perfect predictions for the synthetic CI path."""
    return [
        {"category": "contact"},
        {"category": "invoice"},
        {"category": "support"},
        {"category": "unknown"},
    ]


def _real_predictions() -> list[dict]:
    """Invoke the email-parse agent for each golden row.

    Uses the configured chat model (Ollama by default). Wrapped in a
    per-row ``try/except`` so a single bad row doesn't take down the
    whole run; the failed row counts as ``category='unknown'``.
    """
    from ai_service.agents.email_parse import build_email_parse_graph

    graph = build_email_parse_graph()
    rows = [
        json.loads(line)
        for line in GOLDEN_PATH.read_text().splitlines()
        if line.strip()
    ]
    predictions: list[dict] = []
    for row in rows:
        try:
            out = graph.invoke({"raw": row["raw"]})  # type: ignore[arg-type]
            predictions.append(
                {"category": out.get("result", {}).get("category", "unknown")}
            )
        except Exception:  # noqa: BLE001
            predictions.append({"category": "unknown"})
    return predictions


def collect_predictions() -> list[dict]:
    """Return the prediction list for the current run mode.

    Returns:
        One ``{category}`` dict per golden row.
    """
    if os.environ.get("MAKE_REAL") == "1":
        return _real_predictions()
    return _synthetic_predictions()


def main() -> None:
    """Run the eval and write ``last_ok`` when thresholds are met.

    Raises:
        SystemExit: on regression below the configured threshold.
    """
    thresholds = yaml.safe_load(THRESHOLDS_PATH.read_text())
    predictions = collect_predictions()
    metrics = eval_email_parse(GOLDEN_PATH, predictions)
    threshold = float(thresholds.get("email_parse_macro_f1", 0.0))
    if metrics["macro_f1"] < threshold:
        raise SystemExit(
            f"regression: macro_f1={metrics['macro_f1']:.3f} "
            f"< threshold {threshold:.3f}"
        )
    LAST_OK_MARKER.write_text("ok\n")
    print(f"OK: macro_f1={metrics['macro_f1']:.3f} >= {threshold:.3f}")


if __name__ == "__main__":
    main()
