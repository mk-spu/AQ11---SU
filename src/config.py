# =============================================================================
# config.py — AQ11 Project Configuration
# =============================================================================
# Central configuration file. Change these values to adjust
# dataset size, noise, experiment settings, and output paths.
# =============================================================================

import os

# ─── Dataset ──────────────────────────────────────────────────────────────────
DATASET_SIZE        = 1000       # Total number of samples
NOISE_RATIO         = 0.00       # Fraction of labels to flip (0.0 = no noise)
TEST_SPLIT          = 0.20       # Fraction of data held out for testing
RANDOM_SEED         = 42         # Reproducibility seed

# Feature value range
FEATURE_MIN         = 0.0
FEATURE_MAX         = 10.0

# Classification boundary (used by dataset generator AND AQ11 candidate search)
BOUNDARY_X          = 4.5
BOUNDARY_Y          = 4.5

# ─── AQ11 Algorithm ───────────────────────────────────────────────────────────
BEAM_WIDTH          = 8          # Maximum candidates in the star at one time
MAX_RULES           = 20         # Stop if we generate this many rules
MIN_COVERAGE        = 0.005      # A rule must cover at least 0.5% of positives
CANDIDATE_THRESHOLDS = 10        # Number of threshold values tested per feature

# ─── Visualisation ────────────────────────────────────────────────────────────
DPI                 = 150        # Output image resolution
FIGURE_SIZE         = (10, 7)    # Default figure size (inches)
COLOR_CLASS0        = "#4C9BE8"  # Blue  — negative class
COLOR_CLASS1        = "#E8734C"  # Orange — positive class
COLOR_BOUNDARY      = "#2ECC71"  # Green — decision boundary

# ─── Experiment sizes ─────────────────────────────────────────────────────────
EXPERIMENT_SIZES    = [160, 400, 800, 1000, 1800]

# ─── Output paths ─────────────────────────────────────────────────────────────
OUTPUT_DIR = "results"
GRAPH_DIR = "results/graphs"
JSON_OUTPUT_PATH = "data/data.json"

# Auto-create output directories
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(GRAPH_DIR, exist_ok=True)
