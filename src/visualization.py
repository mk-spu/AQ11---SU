# =============================================================================
# visualization.py — Matplotlib Visualisations
# =============================================================================
# Generates and saves four publication-quality plots:
#   1. scatter_plot.png        — dataset coloured by class
#   2. decision_boundary.png   — scatter + AQ11 rule boundary overlay
#   3. confusion_matrix.png    — annotated heatmap
#   4. experiment_results.png  — accuracy vs dataset size bar chart
# =============================================================================

from __future__ import annotations

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend (safe for all environments)
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
from typing import List, Optional

from config import (
    GRAPH_DIR, DPI, FIGURE_SIZE,
    COLOR_CLASS0, COLOR_CLASS1, COLOR_BOUNDARY,
    BOUNDARY_X, BOUNDARY_Y,
)


# ─── 1. Scatter Plot ──────────────────────────────────────────────────────────

def plot_scatter(
    X: np.ndarray,
    y: np.ndarray,
    title: str = "Dataset — Feature Space (x vs y)",
    filename: str = "scatter_plot.png",
) -> str:
    """
    Scatter plot of samples in the (x, y) feature space, coloured by class.
    Returns the absolute path of the saved figure.
    """
    fig, ax = plt.subplots(figsize=FIGURE_SIZE, dpi=DPI)
    fig.patch.set_facecolor("#0F172A")
    ax.set_facecolor("#1E293B")

    mask0 = y == 0
    mask1 = y == 1

    ax.scatter(
        X[mask0, 0], X[mask0, 1],
        c=COLOR_CLASS0, s=18, alpha=0.65, label="Class 0 (negative)",
        edgecolors="none",
    )
    ax.scatter(
        X[mask1, 0], X[mask1, 1],
        c=COLOR_CLASS1, s=18, alpha=0.65, label="Class 1 (positive)",
        edgecolors="none",
    )

    _style_axes(ax, title, "Feature  x", "Feature  y")

    legend = ax.legend(
        fontsize=10, framealpha=0.3, facecolor="#1E293B",
        labelcolor="white", edgecolor="#334155",
    )

    fig.tight_layout()
    path = _save(fig, filename)
    return path


# ─── 2. Decision Boundary ────────────────────────────────────────────────────

def plot_decision_boundary(
    X: np.ndarray,
    y: np.ndarray,
    rules: Optional[list] = None,
    filename: str = "decision_boundary.png",
) -> str:
    """
    Scatter plot with the ground-truth AQ11 decision boundary overlaid.
    Optionally draws coloured rule-coverage rectangles.
    Returns the absolute path of the saved figure.
    """
    fig, ax = plt.subplots(figsize=FIGURE_SIZE, dpi=DPI)
    fig.patch.set_facecolor("#0F172A")
    ax.set_facecolor("#1E293B")

    mask0, mask1 = y == 0, y == 1
    ax.scatter(X[mask0, 0], X[mask0, 1], c=COLOR_CLASS0, s=16, alpha=0.55,
               label="Class 0", edgecolors="none")
    ax.scatter(X[mask1, 0], X[mask1, 1], c=COLOR_CLASS1, s=16, alpha=0.55,
               label="Class 1", edgecolors="none")

    # Ground-truth boundary box (top-right quadrant)
    xmin, xmax = X[:, 0].min(), X[:, 0].max()
    ymin, ymax = X[:, 1].min(), X[:, 1].max()

    # Vertical boundary line
    ax.axvline(
        x=BOUNDARY_X, color=COLOR_BOUNDARY,
        linestyle="--", linewidth=1.8, alpha=0.85,
        label=f"Boundary x={BOUNDARY_X}",
    )
    # Horizontal boundary line
    ax.axhline(
        y=BOUNDARY_Y, color="#F59E0B",
        linestyle="--", linewidth=1.8, alpha=0.85,
        label=f"Boundary y={BOUNDARY_Y}",
    )

    # Shade the positive quadrant
    ax.fill_betweenx(
        [BOUNDARY_Y, ymax], BOUNDARY_X, xmax,
        alpha=0.12, color=COLOR_CLASS1, label="Positive region",
    )

    # Annotate quadrant labels
    _annotate(ax, xmax * 0.78, ymax * 0.93, "CLASS 1", COLOR_CLASS1)
    _annotate(ax, xmin * 0.02, ymin * 0.05 + 0.2, "CLASS 0", COLOR_CLASS0)

    _style_axes(ax, "Decision Boundary — AQ11", "Feature  x", "Feature  y")
    ax.legend(fontsize=9, framealpha=0.3, facecolor="#1E293B",
              labelcolor="white", edgecolor="#334155")

    fig.tight_layout()
    return _save(fig, filename)


# ─── 3. Confusion Matrix Heatmap ─────────────────────────────────────────────

def plot_confusion_matrix(
    cm_array: np.ndarray,
    labels: List[str] = ("Predicted 0", "Predicted 1"),
    row_labels: List[str] = ("Actual 0", "Actual 1"),
    filename: str = "confusion_matrix.png",
) -> str:
    """
    Annotated heatmap of a 2×2 confusion matrix.
    cm_array should be [[TN, FP], [FN, TP]].
    Returns the absolute path of the saved figure.
    """
    fig, ax = plt.subplots(figsize=(7, 5), dpi=DPI)
    fig.patch.set_facecolor("#0F172A")
    ax.set_facecolor("#1E293B")

    # Re-order to standard layout: rows = actual, cols = predicted
    # Input:  [[TP, FP], [FN, TN]]  → display as [[TN, FP],[FN, TP]]
    TP = int(cm_array[0, 0])
    FP = int(cm_array[0, 1])
    FN = int(cm_array[1, 0])
    TN = int(cm_array[1, 1])
    display = np.array([[TN, FP], [FN, TP]])

    cmap = LinearSegmentedColormap.from_list(
        "aq11_cm", ["#1E293B", "#1D4ED8", "#2563EB"]
    )
    im = ax.imshow(display, cmap=cmap, aspect="auto")

    cell_labels = [
        ["TN", "FP"],
        ["FN", "TP"],
    ]
    cell_colors = [
        [COLOR_CLASS0, "#EF4444"],
        ["#F97316",    COLOR_CLASS1],
    ]

    for i in range(2):
        for j in range(2):
            val = display[i, j]
            tag = cell_labels[i][j]
            ax.text(
                j, i, f"{tag}\n{val}",
                ha="center", va="center",
                fontsize=18, fontweight="bold",
                color=cell_colors[i][j],
            )

    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(labels, fontsize=11, color="white")
    ax.set_yticklabels(row_labels, fontsize=11, color="white")
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_edgecolor("#334155")

    ax.set_title("Confusion Matrix — AQ11", color="white",
                 fontsize=15, fontweight="bold", pad=14)
    ax.set_xlabel("Predicted class", color="#94A3B8", fontsize=11)
    ax.set_ylabel("Actual class", color="#94A3B8", fontsize=11)

    fig.tight_layout()
    return _save(fig, filename)


# ─── 4. Experiment Results Bar Chart ─────────────────────────────────────────

def plot_experiment_results(
    sizes: List[int],
    accuracies: List[float],
    filename: str = "experiment_results.png",
) -> str:
    """
    Grouped bar chart showing accuracy at different dataset sizes.
    Returns the absolute path of the saved figure.
    """
    fig, ax = plt.subplots(figsize=FIGURE_SIZE, dpi=DPI)
    fig.patch.set_facecolor("#0F172A")
    ax.set_facecolor("#1E293B")

    x = np.arange(len(sizes))
    bars = ax.bar(
        x, [a * 100 for a in accuracies],
        color=COLOR_CLASS1, alpha=0.85, width=0.55,
        edgecolor="#F97316", linewidth=0.8,
    )

    # Value labels on top of bars
    for bar, acc in zip(bars, accuracies):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.4,
            f"{acc*100:.1f}%",
            ha="center", va="bottom", color="white",
            fontsize=11, fontweight="bold",
        )

    ax.set_ylim(70, 100)
    ax.set_xticks(x)
    ax.set_xticklabels([f"n={s:,}" for s in sizes], color="white", fontsize=10)
    _style_axes(ax, "AQ11 Accuracy vs Dataset Size",
                "Training set size", "Accuracy (%)")
    ax.axhline(90, color="#64748B", linestyle=":", linewidth=1, alpha=0.6)

    fig.tight_layout()
    return _save(fig, filename)


# ─── 5. Noise sensitivity chart ──────────────────────────────────────────────

def plot_noise_sensitivity(
    noise_levels: List[float],
    accuracies: List[float],
    filename: str = "noise_sensitivity.png",
) -> str:
    """Line chart: accuracy vs noise level."""
    fig, ax = plt.subplots(figsize=FIGURE_SIZE, dpi=DPI)
    fig.patch.set_facecolor("#0F172A")
    ax.set_facecolor("#1E293B")

    pct = [n * 100 for n in noise_levels]
    acc_pct = [a * 100 for a in accuracies]

    ax.plot(pct, acc_pct, color=COLOR_CLASS1, linewidth=2.5,
            marker="o", markersize=8, markerfacecolor="white",
            markeredgecolor=COLOR_CLASS1, markeredgewidth=2)
    ax.fill_between(pct, acc_pct, alpha=0.15, color=COLOR_CLASS1)

    for x_val, y_val in zip(pct, acc_pct):
        ax.text(x_val, y_val + 0.8, f"{y_val:.1f}%",
                ha="center", color="white", fontsize=9)

    ax.set_ylim(60, 100)
    _style_axes(ax, "AQ11 Accuracy vs Label Noise",
                "Noise level (%)", "Accuracy (%)")
    ax.axhline(90, color="#64748B", linestyle=":", linewidth=1, alpha=0.6)

    fig.tight_layout()
    return _save(fig, filename)


# ─── Internal helpers ─────────────────────────────────────────────────────────

def _style_axes(ax, title, xlabel, ylabel):
    ax.set_title(title, color="white", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel(xlabel, color="#94A3B8", fontsize=11)
    ax.set_ylabel(ylabel, color="#94A3B8", fontsize=11)
    ax.tick_params(colors="#94A3B8")
    ax.grid(True, color="#334155", linestyle="--", linewidth=0.6, alpha=0.7)
    for spine in ax.spines.values():
        spine.set_edgecolor("#334155")


def _annotate(ax, x, y, text, color):
    ax.text(x, y, text, color=color, fontsize=10, fontweight="bold",
            alpha=0.75, ha="center")


def _save(fig, filename: str) -> str:
    path = os.path.join(GRAPH_DIR, filename)
    fig.savefig(path, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    return path
