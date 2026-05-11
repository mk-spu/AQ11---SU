# AQ11 — Rule Generation Algorithm

> **University demo project** — Python implementation of the AQ11 symbolic
> machine-learning algorithm with interactive visualisations and a JSON export
> that feeds directly into the companion web dashboard.

---

## What is AQ11?

AQ11 is a **rule-learning algorithm** developed by Ryszard Michalski (1978)
at the University of Illinois.  It belongs to the family of *sequential
covering* (also called *separate-and-conquer*) algorithms for symbolic
machine learning.

Unlike black-box models (neural networks, gradient boosting), AQ11 produces
**explicit IF-THEN rules** that are directly readable by humans:

```
IF x > 5.23 AND y > 4.87  THEN class = 1   [cov=34.2%  conf=97.1%]
IF x > 4.50 AND y > 5.12  THEN class = 1   [cov=21.8%  conf=95.4%]
...
```

This makes it ideal for applications in medicine, law, and finance where
model transparency is legally or ethically required.

### Algorithm sketch

```
E⁺ ← positive examples,  E⁻ ← negative examples
R  ← {}
while E⁺ is not empty:
    seed  ← random sample from E⁺
    star  ← Star(seed, E⁻)          # generate consistent candidates
    R*    ← argmax Q(r) for r in star
    R     ← R ∪ {R*}
    E⁺    ← E⁺ \ covered(R*)
return R
```

---

## Project Structure

```
aq11_project/
│
├── main.py            ← Entry point — run this
├── config.py          ← All tunable parameters (sizes, paths, colours…)
├── dataset.py         ← Synthetic dataset generator
├── aq11.py            ← AQ11 sequential covering implementation
├── metrics.py         ← Accuracy, precision, recall, F1, confusion matrix
├── visualization.py   ← Matplotlib graphs (saved as PNG)
├── export.py          ← Serialise results to JSON for the web dashboard
│
├── requirements.txt
├── README.md
│
└── outputs/
    ├── data.json                     ← Web-dashboard data feed
    └── graphs/
        ├── scatter_plot.png
        ├── decision_boundary.png
        ├── confusion_matrix.png
        ├── experiment_results.png
        └── noise_sensitivity.png
```

### File responsibilities

| File | Responsibility |
|------|---------------|
| `config.py` | Single source of truth for all parameters. Change values here, not inside other files. |
| `dataset.py` | Generates a binary-class synthetic dataset with features `x`, `y`, `hair`, `eyes`. Ground-truth rule: `class=1 iff x>4.5 AND y>4.5`. Supports configurable noise. |
| `aq11.py` | Full AQ11 implementation: `Selector`, `Rule` data classes + `AQ11Classifier` with `fit()` / `predict()` interface. |
| `metrics.py` | Pure-NumPy computation of TP/TN/FP/FN and all derived metrics. No sklearn dependency for core maths. |
| `visualization.py` | Five dark-themed Matplotlib figures saved to `outputs/graphs/`. |
| `export.py` | Builds and writes `outputs/data.json` consumed by the web dashboard. |
| `main.py` | Orchestrates the full pipeline with a colourful, animated CLI. |

---

## Quickstart

### 1 — Install dependencies

```bash
pip install -r requirements.txt
```

> Python ≥ 3.10 recommended.

### 2 — Run the demo

```bash
python main.py
```

### 3 — Optional flags

| Flag | Default | Description |
|------|---------|-------------|
| `--size N` | 1000 | Dataset size |
| `--noise F` | 0.10 | Label noise fraction (0.0 – 1.0) |
| `--no-graphs` | off | Skip PNG generation |
| `--verbose` | off | Show per-rule AQ11 training output |

```bash
# Examples
python main.py --size 500 --noise 0.05
python main.py --size 2000 --no-graphs
python main.py --verbose
```

---

## Expected Output (terminal)

```
══════════════════════════════════════════════════════════════
  STEP 1 / 5  ·  DATASET GENERATION
══════════════════════════════════════════════════════════════
  →  Generating synthetic dataset  (n=1000, noise=10%)
  Generating samples  [████████████████████████] done
  Samples  : 1,000
  Features : x, y, hair, eyes
  Noise    : 10%
  ...

══════════════════════════════════════════════════════════════
  STEP 3 / 5  ·  EVALUATION METRICS
══════════════════════════════════════════════════════════════
  Accuracy        94.00%    ████████████████████
  Precision       94.16%    ████████████████████
  Recall          95.39%    ████████████████████
  F1 Score        94.77%    ████████████████████
```

---

## Generated Outputs

After running `main.py`, the `outputs/` directory will contain:

### `data.json`

```json
{
  "_meta": { "generated_at": "...", "project": "AQ11 Rule Learning" },
  "dataset": { "metadata": {...}, "sample": [...] },
  "rules": [
    {
      "conditions": ["x > 5.23", "y > 4.87"],
      "conclusion": "class = 1",
      "coverage_pct": 34.2,
      "confidence_pct": 97.1
    }
  ],
  "metrics": { "TP": 290, "TN": 278, "FP": 18, "FN": 14, "accuracy": 0.94 },
  "experiments": { "size_experiment": [...], "noise_experiment": [...] }
}
```

### Graphs

| File | Description |
|------|-------------|
| `scatter_plot.png` | Dataset coloured by class in (x, y) space |
| `decision_boundary.png` | Scatter + AQ11 decision boundary overlay |
| `confusion_matrix.png` | Annotated TP/TN/FP/FN heatmap |
| `experiment_results.png` | Accuracy vs dataset size bar chart |
| `noise_sensitivity.png` | Accuracy vs noise level line chart |

---

## Connection to Web Dashboard

The `outputs/data.json` file is the bridge between this Python project
and the interactive web dashboard hosted at:

```
https://aq11-web-app-frbzcbgce7g5gvff.polandcentral-01.azurewebsites.net
```

The dashboard reads this JSON to render:
- the rule table (IF-THEN rules with coverage & confidence)
- the confusion matrix widget
- the scatter plot and decision boundary
- the experiment comparison charts

---

## Key Results (reference run, n=1000, noise=10%)

| Metric | Value |
|--------|-------|
| Accuracy | 94.0% |
| Precision | 94.2% |
| Recall | 95.4% |
| F1 Score | 94.8% |
| TP / TN / FP / FN | 290 / 278 / 18 / 14 |
| Rules generated | ~9 |

---

## References

- Michalski, R. S. (1978). *A Theory and Methodology of Inductive Learning.*
  Artificial Intelligence, 11(1–2), 111–161.
- Fürnkranz, J., Gamberger, D., & Lavrač, N. (2012).
  *Foundations of Rule Learning.* Springer.
- Molnar, C. (2022). *Interpretable Machine Learning* (2nd ed.).
>>>>>>> 6bb1015 (Final AQ11 project structure)
