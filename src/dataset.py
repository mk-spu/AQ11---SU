# =============================================================================
# dataset.py — Synthetic Dataset Generator
# =============================================================================
# Generates a binary-classification dataset with four features:
#   x, y   — continuous spatial features (primary discriminators)
#   hair   — categorical: {0=dark, 1=light}
#   eyes   — categorical: {0=brown, 1=blue, 2=green}
#
# Ground-truth rule:  class = 1  iff  x > BOUNDARY_X  AND  y > BOUNDARY_Y
# Noise: a NOISE_RATIO fraction of labels is randomly flipped.
# =============================================================================

import numpy as np
from sklearn.model_selection import train_test_split
from config import (
    DATASET_SIZE, NOISE_RATIO, TEST_SPLIT, RANDOM_SEED,
    FEATURE_MIN, FEATURE_MAX, BOUNDARY_X, BOUNDARY_Y,
)


# ─── Public API ───────────────────────────────────────────────────────────────

def generate_dataset(
    n_samples: int = DATASET_SIZE,
    noise_ratio: float = NOISE_RATIO,
    seed: int = RANDOM_SEED,
) -> dict:
    """
    Generate a synthetic dataset and return it as a dictionary.

    Returns
    -------
    dict with keys:
        X        — (n, 4) float array  [x, y, hair, eyes]
        y        — (n,)   int   labels {0, 1}
        feature_names — list of column names
        metadata — generation parameters
    """
    rng = np.random.default_rng(seed)

    n_pos = n_samples // 2         # ~50% positive
    n_neg = n_samples - n_pos      # ~50% negative

    # Positive class: x and y both clearly above the boundary
    x_pos = rng.normal(6.5, 1.2, size=n_pos)
    y_pos = rng.normal(6.5, 1.2, size=n_pos)

    # Negative class: at least one of x, y is below the boundary
    x_neg = rng.normal(3.0, 1.3, size=n_neg)
    y_neg = rng.normal(3.0, 1.3, size=n_neg)

    x = np.clip(np.concatenate([x_pos, x_neg]), FEATURE_MIN, FEATURE_MAX)
    y = np.clip(np.concatenate([y_pos, y_neg]), FEATURE_MIN, FEATURE_MAX)

    # Shuffle both arrays with the same permutation to keep pairing
    perm = rng.permutation(n_samples)
    x, y = x[perm], y[perm]

    # Categorical features (not used by the ground-truth rule — serve as
    # distractors that AQ11 must learn to ignore or use secondarily).
    hair = rng.integers(0, 2, size=n_samples).astype(float)   # 0 = dark, 1 = light
    eyes = rng.integers(0, 3, size=n_samples).astype(float)   # 0=brown,1=blue,2=green

    X = np.column_stack([x, y, hair, eyes])

    # Ground-truth labels
    labels = ((x > BOUNDARY_X) & (y > BOUNDARY_Y)).astype(int)

    # Inject label noise
    if noise_ratio > 0.0:
        labels = _add_noise(labels, noise_ratio, rng)

    return {
        "X": X,
        "y": labels,
        "feature_names": ["x", "y", "hair", "eyes"],
        "metadata": {
            "n_samples": n_samples,
            "noise_ratio": noise_ratio,
            "seed": seed,
            "boundary_x": BOUNDARY_X,
            "boundary_y": BOUNDARY_Y,
            "class_counts": {
                "class_0": int((labels == 0).sum()),
                "class_1": int((labels == 1).sum()),
            },
        },
    }


def split_dataset(dataset: dict, test_size: float = TEST_SPLIT, seed: int = RANDOM_SEED):
    """
    Split a dataset dict into train/test portions.

    Returns
    -------
    (X_train, X_test, y_train, y_test)
    """
    return train_test_split(
        dataset["X"],
        dataset["y"],
        test_size=test_size,
        random_state=seed,
        stratify=dataset["y"],
    )


def dataset_summary(dataset: dict) -> str:
    """Return a human-readable summary string."""
    meta = dataset["metadata"]
    c = meta["class_counts"]
    lines = [
        f"  Samples  : {meta['n_samples']:,}",
        f"  Features : {', '.join(dataset['feature_names'])}",
        f"  Noise    : {meta['noise_ratio']*100:.0f}%",
        f"  Class 0  : {c['class_0']:,}  ({c['class_0']/meta['n_samples']*100:.1f}%)",
        f"  Class 1  : {c['class_1']:,}  ({c['class_1']/meta['n_samples']*100:.1f}%)",
        f"  Boundary : x > {meta['boundary_x']} AND y > {meta['boundary_y']}",
    ]
    return "\n".join(lines)


# ─── Internal helpers ─────────────────────────────────────────────────────────

def _gaussian_mixture(rng, n, center_low, center_high, std=1.4):
    """
    Draw samples from a two-component Gaussian mixture so that roughly half
    the samples fall on each side of the classification boundary.
    """
    n_low  = n // 2
    n_high = n - n_low
    low  = rng.normal(center_low,  std, size=n_low)
    high = rng.normal(center_high, std, size=n_high)
    combined = np.concatenate([low, high])
    # Clip to [FEATURE_MIN, FEATURE_MAX] and shuffle
    combined = np.clip(combined, FEATURE_MIN, FEATURE_MAX)
    rng.shuffle(combined)
    return combined


def _add_noise(labels: np.ndarray, ratio: float, rng) -> np.ndarray:
    """Randomly flip `ratio` fraction of labels."""
    noisy = labels.copy()
    n_flip = int(len(labels) * ratio)
    flip_idx = rng.choice(len(labels), size=n_flip, replace=False)
    noisy[flip_idx] = 1 - noisy[flip_idx]
    return noisy
