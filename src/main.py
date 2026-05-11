#!/usr/bin/env python3
# =============================================================================
# main.py — AQ11 Rule Generation Demo  (entry point)
# =============================================================================
# Run with:   python main.py
# Optional :  python main.py --size 500 --noise 0.15 --no-graphs
# =============================================================================

from __future__ import annotations

import argparse
import sys
import time

import numpy as np

from config import (
    DATASET_SIZE, NOISE_RATIO, TEST_SPLIT,
    EXPERIMENT_SIZES, RANDOM_SEED,
)
from dataset import generate_dataset, split_dataset, dataset_summary
from aq11 import AQ11Classifier
from metrics import compute_confusion_matrix
from visualization import (
    plot_scatter,
    plot_decision_boundary,
    plot_confusion_matrix,
    plot_experiment_results,
    plot_noise_sensitivity,
)
from export import build_export_payload, save_to_json


# ─── Terminal styling helpers ─────────────────────────────────────────────────

CYAN    = "\033[96m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
MAGENTA = "\033[95m"
RED     = "\033[91m"
BLUE    = "\033[94m"
WHITE   = "\033[97m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
RESET   = "\033[0m"

W = 62  # box width

def header(text: str) -> None:
    print(f"\n{CYAN}{'═'*W}{RESET}")
    print(f"{BOLD}{CYAN}  {text}{RESET}")
    print(f"{CYAN}{'═'*W}{RESET}")

def section(text: str) -> None:
    print(f"\n{BLUE}  ── {text} {'─'*(W-6-len(text))}{RESET}")

def ok(text: str) -> None:
    print(f"  {GREEN}✓{RESET}  {text}")

def info(text: str) -> None:
    print(f"  {DIM}{YELLOW}→{RESET}  {text}")

def rule_line(text: str) -> None:
    print(f"  {MAGENTA}▸{RESET}  {text}")

def metric_row(label: str, value: str, bar: float = 0.0) -> None:
    filled  = int(bar * 20)
    bar_str = f"{GREEN}{'█'*filled}{DIM}{'░'*(20-filled)}{RESET}"
    print(f"  {WHITE}{label:<14}{RESET} {YELLOW}{value:<10}{RESET}  {bar_str}")

def progress_bar(label: str, total: int = 30, delay: float = 0.035) -> None:
    """Animated progress bar."""
    sys.stdout.write(f"  {DIM}{label}{RESET}  [")
    sys.stdout.flush()
    for _ in range(total):
        time.sleep(delay)
        sys.stdout.write(f"{GREEN}█{RESET}")
        sys.stdout.flush()
    sys.stdout.write("] done\n")
    sys.stdout.flush()


# ─── Main demo ───────────────────────────────────────────────────────────────

def run_demo(
    size: int   = DATASET_SIZE,
    noise: float = NOISE_RATIO,
    save_graphs: bool = True,
    verbose_aq11: bool = False,
) -> None:
    """
    Full demonstration pipeline:
        1. Banner
        2. Dataset generation
        3. AQ11 training
        4. Metrics
        5. Experiments (size + noise)
        6. Visualisations
        7. JSON export
    """

    # ── 0. Banner ──────────────────────────────────────────────────────────────
    print(f"\n{CYAN}{'▓'*W}{RESET}")
    print(f"{BOLD}{CYAN}")
    print(r"   ___  ___  __ ___    ___ _   _ _    ___    ___  ___ __  _  _  ___ ")
    print(r"  | _ \| | | |  | |   | _ \ | | | |  | __|  |   \| __|  \| \/ |/ _ \ ")
    print(r"  |   /| |_| | | |    |   / |_| | |__| _|   | |) | _|| ' \ >< | (_) |")
    print(r"  |_|_\ \_,_/ |_|    |_|_\ \___/|____|___|  |___/|___|_|\_/_/\_\___/ ")
    print(f"{RESET}")
    print(f"  {DIM}AQ11 Rule Generation Algorithm — University Demo Project{RESET}")
    print(f"  {DIM}Based on Michalski (1978) — Sequential Covering{RESET}")
    print(f"{CYAN}{'▓'*W}{RESET}\n")
    time.sleep(0.6)

    # ── 1. Dataset ─────────────────────────────────────────────────────────────
    header("STEP 1 / 5  ·  DATASET GENERATION")
    info(f"Generating synthetic dataset  (n={size:,}, noise={noise*100:.0f}%  {'[clean run]' if noise==0 else ''})")
    progress_bar("Generating samples", total=25, delay=0.02)

    dataset = generate_dataset(n_samples=size, noise_ratio=noise)
    X_train, X_test, y_train, y_test = split_dataset(dataset)

    print(dataset_summary(dataset))
    ok(f"Train / Test split  →  {len(X_train):,} / {len(X_test):,} samples")
    time.sleep(0.3)

    # ── 2. AQ11 Training ───────────────────────────────────────────────────────
    header("STEP 2 / 5  ·  AQ11 RULE GENERATION")
    info("Running sequential covering (AQ11 algorithm)…")
    time.sleep(0.4)
    print()

    clf = AQ11Classifier(verbose=verbose_aq11)
    t0  = time.perf_counter()
    clf.fit(X_train, y_train, feature_names=dataset["feature_names"])
    elapsed = (time.perf_counter() - t0) * 1_000

    n_rules = len(clf.get_rules())
    ok(f"Training complete in  {elapsed:.1f} ms")
    ok(f"Rules generated      :  {n_rules}")
    time.sleep(0.2)

    section("Generated IF-THEN Rules")
    clf.print_rules()
    time.sleep(0.3)

    # ── 3. Metrics ─────────────────────────────────────────────────────────────
    header("STEP 3 / 5  ·  EVALUATION METRICS")
    progress_bar("Evaluating on test set", total=20, delay=0.025)

    y_pred = clf.predict(X_test)
    cm = compute_confusion_matrix(y_test, y_pred)

    print(cm)  # Uses __str__ with the box layout
    print()
    metric_row("Accuracy",  f"{cm.accuracy  *100:.2f}%", cm.accuracy)
    metric_row("Precision", f"{cm.precision *100:.2f}%", cm.precision)
    metric_row("Recall",    f"{cm.recall    *100:.2f}%", cm.recall)
    metric_row("F1 Score",  f"{cm.f1_score  *100:.2f}%", cm.f1_score)
    time.sleep(0.3)

    # ── 4. Experiments ─────────────────────────────────────────────────────────
    header("STEP 4 / 5  ·  EXPERIMENTS")

    # 4a. Dataset size experiment
    section("Experiment A — Dataset Size vs Accuracy")
    experiment_history = []
    for n in EXPERIMENT_SIZES:
        ds  = generate_dataset(n_samples=n, noise_ratio=0.0, seed=RANDOM_SEED)
        Xtr, Xte, ytr, yte = split_dataset(ds)
        c   = AQ11Classifier(verbose=False).fit(Xtr, ytr, dataset["feature_names"])
        yp  = c.predict(Xte)
        m   = compute_confusion_matrix(yte, yp)
        experiment_history.append({
            "size":      n,
            "accuracy":  round(m.accuracy,  4),
            "precision": round(m.precision, 4),
            "recall":    round(m.recall,    4),
            "f1_score":  round(m.f1_score,  4),
            "n_rules":   len(c.get_rules()),
        })
        bar = "█" * int(m.accuracy * 25)
        print(f"    n={n:>5,}  acc={m.accuracy*100:.1f}%  {GREEN}{bar}{RESET}")
        time.sleep(0.12)

    # 4b. Noise sensitivity experiment
    section("Experiment B — Noise Sensitivity")
    noise_levels = [0.0, 0.05, 0.10, 0.20, 0.30]
    noise_history = []
    for nl in noise_levels:
        ds  = generate_dataset(n_samples=size, noise_ratio=nl, seed=RANDOM_SEED)
        Xtr, Xte, ytr, yte = split_dataset(ds)
        c   = AQ11Classifier(verbose=False).fit(Xtr, ytr, dataset["feature_names"])
        yp  = c.predict(Xte)
        m   = compute_confusion_matrix(yte, yp)
        noise_history.append({
            "noise":    nl,
            "accuracy": round(m.accuracy, 4),
            "n_rules":  len(c.get_rules()),
        })
        bar = "█" * int(m.accuracy * 25)
        print(f"    noise={nl*100:>4.0f}%  acc={m.accuracy*100:.1f}%  "
              f"rules={len(c.get_rules()):>2}  {YELLOW}{bar}{RESET}")
        time.sleep(0.12)

    # ── 5. Visualisations ──────────────────────────────────────────────────────
    header("STEP 5 / 5  ·  VISUALISATIONS & EXPORT")

    if save_graphs:
        section("Generating graphs")
        p = plot_scatter(dataset["X"], dataset["y"])
        ok(f"Scatter plot         →  {p}")
        time.sleep(0.15)

        p = plot_decision_boundary(dataset["X"], dataset["y"], clf.get_rules())
        ok(f"Decision boundary    →  {p}")
        time.sleep(0.15)

        p = plot_confusion_matrix(cm.to_array())
        ok(f"Confusion matrix     →  {p}")
        time.sleep(0.15)

        p = plot_experiment_results(
            [e["size"] for e in experiment_history],
            [e["accuracy"] for e in experiment_history],
        )
        ok(f"Experiment chart     →  {p}")
        time.sleep(0.15)

        p = plot_noise_sensitivity(
            [n["noise"] for n in noise_history],
            [n["accuracy"] for n in noise_history],
        )
        ok(f"Noise sensitivity    →  {p}")
        time.sleep(0.15)
    else:
        info("Graph generation skipped (--no-graphs)")

    # JSON export
    section("Exporting JSON for web dashboard")
    payload = build_export_payload(
        dataset_meta       = dataset["metadata"],
        X_sample           = dataset["X"][:20],
        y_sample           = dataset["y"][:20],
        feature_names      = dataset["feature_names"],
        rules              = clf.get_rules(),
        metrics            = cm.as_dict(),
        experiment_history = experiment_history,
        noise_history      = noise_history,
    )
    json_path = save_to_json(payload)
    ok(f"data.json saved      →  {json_path}")

    # ── Summary ────────────────────────────────────────────────────────────────
    print(f"\n{CYAN}{'═'*W}{RESET}")
    print(f"{BOLD}{GREEN}  ✔  DEMO COMPLETE{RESET}")
    print(f"{CYAN}{'─'*W}{RESET}")
    print(f"  Dataset      : {size:,} samples  |  noise = {noise*100:.0f}%")
    print(f"  Rules        : {n_rules}  generated by AQ11")
    print(f"  Accuracy     : {cm.accuracy  *100:.2f}%")
    print(f"  Precision    : {cm.precision *100:.2f}%")
    print(f"  Recall       : {cm.recall    *100:.2f}%")
    print(f"  F1 Score     : {cm.f1_score  *100:.2f}%")
    print(f"  TP={cm.TP}  TN={cm.TN}  FP={cm.FP}  FN={cm.FN}")
    print(f"{CYAN}{'═'*W}{RESET}\n")


# ─── CLI argument parsing ────────────────────────────────────────────────────

def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="AQ11 Rule Generation Demo")
    p.add_argument(
        "--size",  type=int,   default=DATASET_SIZE,
        help=f"Dataset size (default: {DATASET_SIZE})",
    )
    p.add_argument(
        "--noise", type=float, default=NOISE_RATIO,
        help=f"Label noise fraction 0.0–1.0 (default: {NOISE_RATIO})",
    )
    p.add_argument(
        "--no-graphs", action="store_true",
        help="Skip matplotlib graph generation",
    )
    p.add_argument(
        "--verbose", action="store_true",
        help="Show AQ11 rule-by-rule verbose output during training",
    )
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    run_demo(
        size        = args.size,
        noise       = args.noise,
        save_graphs = not args.no_graphs,
        verbose_aq11= args.verbose,
    )
