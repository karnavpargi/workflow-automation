"""Offline eval over golden fixtures and recorded predictions.

Free/OSS only: ``pandas`` + ``scikit-learn``. No network calls; the
runner compares predictions against a JSONL golden set and reports
classification metrics. A future task wires LangSmith-exported
predictions as the input.
"""

import json
from pathlib import Path

import pandas as pd
from sklearn.metrics import classification_report, f1_score


def load_golden(path: Path) -> pd.DataFrame:
    """Load a JSONL golden set into a DataFrame.

    Args:
        path: Path to a ``.jsonl`` file with one record per line.

    Returns:
        DataFrame with at least the columns ``raw`` and ``category``.
    """
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    return pd.DataFrame(rows)


def eval_email_parse(golden_path: Path, predictions: list[dict]) -> dict:
    """Compute macro F1 + per-class report for the email-parse agent.

    Args:
        golden_path: JSONL with ``{raw, category}`` rows.
        predictions: Aligned ``{category}`` dicts, same length as golden.

    Returns:
        ``{"macro_f1": float, "per_class": str}``.
    """
    golden = load_golden(golden_path)
    gold_labels = golden["category"].tolist()
    pred_labels = [p["category"] for p in predictions]
    return {
        "macro_f1": float(
            f1_score(gold_labels, pred_labels, average="macro", zero_division=0)
        ),
        "per_class": classification_report(gold_labels, pred_labels, zero_division=0),
    }
