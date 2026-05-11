# =============================================================================
# metrics.py — Classification Metrics
# =============================================================================
# Computes accuracy, precision, recall, F1 score and a confusion matrix
# WITHOUT relying on sklearn (pure NumPy), so the maths is transparent.
# =============================================================================

from __future__ import annotations

from dataclasses import dataclass
import numpy as np


# ─── Confusion matrix dataclass ───────────────────────────────────────────────

@dataclass
class ConfusionMatrix:
    """Stores TP, TN, FP, FN and derived metrics for a binary classifier."""

    TP: int
    TN: int
    FP: int
    FN: int

    # ── Derived scalar metrics ────────────────────────────────────────────────

    @property
    def accuracy(self) -> float:
        """(TP + TN) / total"""
        total = self.TP + self.TN + self.FP + self.FN
        return (self.TP + self.TN) / total if total else 0.0

    @property
    def precision(self) -> float:
        """TP / (TP + FP)"""
        denom = self.TP + self.FP
        return self.TP / denom if denom else 0.0

    @property
    def recall(self) -> float:
        """TP / (TP + FN)  — also called sensitivity"""
        denom = self.TP + self.FN
        return self.TP / denom if denom else 0.0

    @property
    def f1_score(self) -> float:
        """Harmonic mean of precision and recall."""
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) else 0.0

    @property
    def specificity(self) -> float:
        """TN / (TN + FP)"""
        denom = self.TN + self.FP
        return self.TN / denom if denom else 0.0

    @property
    def fp_rate(self) -> float:
        """FP / (FP + TN)"""
        denom = self.FP + self.TN
        return self.FP / denom if denom else 0.0

    @property
    def fn_rate(self) -> float:
        """FN / (FN + TP)"""
        denom = self.FN + self.TP
        return self.FN / denom if denom else 0.0

    # ── Representation ────────────────────────────────────────────────────────

    def as_dict(self) -> dict:
        return {
            "TP": self.TP,
            "TN": self.TN,
            "FP": self.FP,
            "FN": self.FN,
            "accuracy":    round(self.accuracy,    4),
            "precision":   round(self.precision,   4),
            "recall":      round(self.recall,      4),
            "f1_score":    round(self.f1_score,    4),
            "specificity": round(self.specificity, 4),
            "fp_rate":     round(self.fp_rate,     4),
            "fn_rate":     round(self.fn_rate,     4),
        }

    def __str__(self) -> str:
        return (
            f"\n  ┌─────────────────────────────────────────┐\n"
            f"  │           CONFUSION MATRIX               │\n"
            f"  ├─────────────────────┬───────────────────┤\n"
            f"  │  TP = {self.TP:>5}  (✓ pos)  │  FP = {self.FP:>4}  (✗ pos) │\n"
            f"  ├─────────────────────┼───────────────────┤\n"
            f"  │  FN = {self.FN:>5}  (✗ neg)  │  TN = {self.TN:>4}  (✓ neg) │\n"
            f"  └─────────────────────┴───────────────────┘\n"
            f"\n  Accuracy   : {self.accuracy  *100:.2f}%"
            f"\n  Precision  : {self.precision *100:.2f}%"
            f"\n  Recall     : {self.recall    *100:.2f}%"
            f"\n  F1 Score   : {self.f1_score  *100:.2f}%"
            f"\n  Specificity: {self.specificity*100:.2f}%"
            f"\n  FP Rate    : {self.fp_rate   *100:.2f}%"
            f"\n  FN Rate    : {self.fn_rate   *100:.2f}%"
        )

    def to_array(self) -> np.ndarray:
        """Return a 2×2 array [[TP, FP], [FN, TN]] for plotting."""
        return np.array([[self.TP, self.FP], [self.FN, self.TN]])


# ─── Public API ───────────────────────────────────────────────────────────────

def compute_confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray) -> ConfusionMatrix:
    """
    Compute a binary confusion matrix.

    Parameters
    ----------
    y_true : ground-truth labels {0, 1}
    y_pred : predicted labels {0, 1}

    Returns
    -------
    ConfusionMatrix instance
    """
    y_true = np.asarray(y_true, dtype=int)
    y_pred = np.asarray(y_pred, dtype=int)

    TP = int(((y_pred == 1) & (y_true == 1)).sum())
    TN = int(((y_pred == 0) & (y_true == 0)).sum())
    FP = int(((y_pred == 1) & (y_true == 0)).sum())
    FN = int(((y_pred == 0) & (y_true == 1)).sum())

    return ConfusionMatrix(TP=TP, TN=TN, FP=FP, FN=FN)


def compute_all_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    """Convenience wrapper — returns a plain dict of all metrics."""
    cm = compute_confusion_matrix(y_true, y_pred)
    return cm.as_dict()
