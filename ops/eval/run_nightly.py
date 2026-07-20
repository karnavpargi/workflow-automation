"""Run the golden-set eval and enforce the configured thresholds.

The runner is intentionally tiny: it loads the JSONL golden set and
``ai_service.eval.harness.eval_email_parse`` against a fixed
prediction vector, then enforces ``thresholds.yaml``. In CI the
prediction vector is filled in by a ``MAKE_REAL=1`` run that talks to
the live LLM; the default test path is the synthetic path that locks
in the contract.

Usage:
    python ops/eval/run_nightly.py
"""

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


def main() -> None:
    """Run the eval and write ``last_ok`` when thresholds are met.

    Raises:
        SystemExit: on regression below the configured threshold.
    """
    thresholds = yaml.safe_load(THRESHOLDS_PATH.read_text())
    predictions = [
        {"category": "contact"},
        {"category": "invoice"},
        {"category": "support"},
        {"category": "unknown"},
    ]
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
