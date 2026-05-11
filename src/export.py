# =============================================================================
# export.py — Results Export
# =============================================================================
# Serialises the full experiment run (dataset sample, generated rules, metrics,
# experiment history) to a structured JSON file that the web dashboard can
# consume directly.
# =============================================================================

from __future__ import annotations

import json
import os
import numpy as np
from datetime import datetime
from typing import Any, List

from config import JSON_OUTPUT_PATH


# ─── Public API ───────────────────────────────────────────────────────────────

def build_export_payload(
    dataset_meta: dict,
    X_sample: np.ndarray,
    y_sample: np.ndarray,
    feature_names: List[str],
    rules: list,           # List[Rule] from aq11.py
    metrics: dict,
    experiment_history: List[dict],
    noise_history: List[dict],
) -> dict:
    """
    Assemble all results into a single, web-ready dictionary.

    Parameters
    ----------
    dataset_meta       : metadata dict from DatasetGenerator
    X_sample           : first N rows for preview (use first 20)
    y_sample           : corresponding labels
    feature_names      : list of column names
    rules              : list of Rule objects
    metrics            : dict from metrics.compute_all_metrics()
    experiment_history : list of {size, accuracy, precision, recall, f1}
    noise_history      : list of {noise, accuracy, n_rules}
    """
    payload = {
        "_meta": {
            "generated_at": datetime.now().isoformat(),
            "project":      "AQ11 Rule Learning",
            "version":      "1.0.0",
        },
        "dataset": {
            "metadata":      dataset_meta,
            "feature_names": feature_names,
            "sample": _format_sample(X_sample, y_sample, feature_names),
        },
        "rules":   _format_rules(rules),
        "metrics": metrics,
        "experiments": {
            "size_experiment":  experiment_history,
            "noise_experiment": noise_history,
        },
    }
    return payload


def save_to_json(payload: dict, path: str = JSON_OUTPUT_PATH) -> str:
    """
    Write the payload to *path* as pretty-printed JSON.
    Returns the resolved absolute path.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False,
                  default=_json_serialiser)
    return os.path.abspath(path)


# ─── Internal helpers ─────────────────────────────────────────────────────────

def _format_sample(
    X: np.ndarray, y: np.ndarray, feature_names: List[str], n: int = 20
) -> List[dict]:
    """Convert the first *n* rows to a list of dicts."""
    rows = []
    for i in range(min(n, len(X))):
        row = {name: round(float(X[i, j]), 4) for j, name in enumerate(feature_names)}
        row["class"] = int(y[i])
        rows.append(row)
    return rows


def _format_rules(rules: list) -> List[dict]:
    """Convert Rule objects to plain dicts."""
    return [r.to_dict() for r in rules]


def _json_serialiser(obj: Any) -> Any:
    """Fallback serialiser for numpy scalars and other non-standard types."""
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    raise TypeError(f"Object of type {type(obj)} is not JSON serialisable")
