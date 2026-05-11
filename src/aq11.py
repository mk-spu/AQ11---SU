# =============================================================================
# aq11.py — AQ11 Rule Learning Algorithm
# =============================================================================
# Implements a faithful, simplified version of the AQ11 (Michalski, 1978)
# sequential covering algorithm for binary classification.
#
# Algorithm outline
# -----------------
# 1. Split training data into E+ (positive) and E- (negative).
# 2. While E+ is not empty:
#    a. Pick a random seed from E+.
#    b. Run the Star algorithm to generate candidate rules that cover the
#       seed and are consistent with E- (i.e., exclude all negatives).
#    c. Select the best rule by a quality function Q(R).
#    d. Add the rule to the rule set; remove covered positives from E+.
# 3. Return the rule set.
# =============================================================================

from __future__ import annotations

import time
import random
import numpy as np
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

from config import (
    BEAM_WIDTH, MAX_RULES, MIN_COVERAGE, CANDIDATE_THRESHOLDS,
    FEATURE_MIN, FEATURE_MAX, RANDOM_SEED,
)


# ─── Data structures ──────────────────────────────────────────────────────────

@dataclass
class Selector:
    """
    A single condition on one feature, e.g. 'x > 4.5'.

    Attributes
    ----------
    feature_idx   : column index in X
    feature_name  : human-readable name
    operator      : '>' or '<='
    threshold     : numeric cut-point
    """
    feature_idx:  int
    feature_name: str
    operator:     str    # '>' | '<='
    threshold:    float

    def covers(self, sample: np.ndarray) -> bool:
        """Return True if this condition is satisfied by *sample*."""
        v = sample[self.feature_idx]
        return v > self.threshold if self.operator == ">" else v <= self.threshold

    def __str__(self) -> str:
        return f"{self.feature_name} {self.operator} {self.threshold:.2f}"


@dataclass
class Rule:
    """
    A conjunctive IF-THEN rule: a list of Selectors → predicted class.

    Attributes
    ----------
    selectors   : conditions (ANDed together)
    target_class: predicted class when all conditions hold
    coverage    : fraction of training positives covered
    confidence  : fraction of covered samples with the correct label
    n_covered   : absolute number of positives covered on training data
    """
    selectors:    List[Selector]
    target_class: int = 1
    coverage:     float = 0.0
    confidence:   float = 0.0
    n_covered:    int   = 0

    def covers(self, sample: np.ndarray) -> bool:
        """Return True iff ALL selectors are satisfied."""
        return all(s.covers(sample) for s in self.selectors)

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Vectorised: return boolean mask of covered samples."""
        return np.array([self.covers(row) for row in X])

    def to_dict(self) -> dict:
        return {
            "conditions": [str(s) for s in self.selectors],
            "conclusion": f"class = {self.target_class}",
            "coverage_pct": round(self.coverage * 100, 1),
            "confidence_pct": round(self.confidence * 100, 1),
            "n_covered": self.n_covered,
        }

    def __str__(self) -> str:
        conds = " AND ".join(str(s) for s in self.selectors)
        return (
            f"IF {conds} "
            f"THEN class = {self.target_class}  "
            f"[cov={self.coverage*100:.1f}%  conf={self.confidence*100:.1f}%]"
        )


# ─── AQ11 Classifier ──────────────────────────────────────────────────────────

class AQ11Classifier:
    """
    Binary AQ11 classifier.

    Parameters
    ----------
    beam_width          : max candidates kept in the star at each step
    max_rules           : hard ceiling on the number of rules generated
    min_coverage        : minimum fraction of E+ a rule must cover
    candidate_thresholds: number of threshold cuts tested per feature
    seed                : random seed for reproducibility
    verbose             : if True, print progress during training
    """

    def __init__(
        self,
        beam_width: int           = BEAM_WIDTH,
        max_rules: int            = MAX_RULES,
        min_coverage: float       = MIN_COVERAGE,
        candidate_thresholds: int = CANDIDATE_THRESHOLDS,
        seed: int                 = RANDOM_SEED,
        verbose: bool             = True,
    ) -> None:
        self.beam_width           = beam_width
        self.max_rules            = max_rules
        self.min_coverage         = min_coverage
        self.candidate_thresholds = candidate_thresholds
        self.seed                 = seed
        self.verbose              = verbose

        self.rules_:         List[Rule] = []
        self.feature_names_: List[str]  = []
        self._rng = random.Random(seed)

    # ── Public interface ──────────────────────────────────────────────────────

    def fit(self, X: np.ndarray, y: np.ndarray, feature_names: Optional[List[str]] = None) -> "AQ11Classifier":
        """
        Train the AQ11 classifier on (X, y).

        Parameters
        ----------
        X              : (n_samples, n_features) training matrix
        y              : (n_samples,) binary labels {0, 1}
        feature_names  : optional list of column names
        """
        n_features = X.shape[1]
        self.feature_names_ = feature_names or [f"f{i}" for i in range(n_features)]
        self.rules_ = []

        # Separate positive and negative indices
        pos_idx = list(np.where(y == 1)[0])
        neg_idx = list(np.where(y == 0)[0])
        total_pos = len(pos_idx)

        if self.verbose:
            print(f"    E+ = {total_pos:,} positive  |  E- = {len(neg_idx):,} negative")

        # Precompute candidate thresholds for each feature (quantile-based)
        thresholds = self._compute_thresholds(X)

        uncovered_pos = set(pos_idx)
        seen_rule_strs: set = set()   # de-duplicate rules

        while uncovered_pos and len(self.rules_) < self.max_rules:
            seed_idx = self._rng.choice(list(uncovered_pos))
            seed_sample = X[seed_idx]

            best_rule = self._star(
                seed_sample, X, y, pos_idx, neg_idx,
                thresholds, total_pos
            )

            if best_rule is None:
                break

            if best_rule.coverage < self.min_coverage:
                break

            # Skip duplicate rules
            rule_sig = str(sorted(str(s) for s in best_rule.selectors))
            if rule_sig in seen_rule_strs:
                uncovered_pos.discard(seed_idx)
                continue
            seen_rule_strs.add(rule_sig)

            self.rules_.append(best_rule)

            newly_covered = {
                i for i in uncovered_pos if best_rule.covers(X[i])
            }
            uncovered_pos -= newly_covered

            if self.verbose:
                remaining_pct = len(uncovered_pos) / total_pos * 100
                print(
                    f"    Rule {len(self.rules_):>2}: {str(best_rule)}"
                    f"\n           → covered {len(newly_covered)} new samples "
                    f"| E+ remaining: {len(uncovered_pos)} ({remaining_pct:.1f}%)"
                )

        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Classify each sample in X.

        Rules are applied in order; the first matching rule fires.
        Samples matched by no rule default to class 0 (negative).
        """
        predictions = np.zeros(len(X), dtype=int)
        for rule in self.rules_:
            mask = rule.predict(X)
            predictions[mask] = rule.target_class
        return predictions

    def get_rules(self) -> List[Rule]:
        return self.rules_

    def print_rules(self) -> None:
        """Pretty-print all rules to stdout."""
        if not self.rules_:
            print("  (no rules generated)")
            return
        for i, rule in enumerate(self.rules_, 1):
            conds = "\n           AND ".join(str(s) for s in rule.selectors)
            print(
                f"  Rule {i:>2}:  IF  {conds}\n"
                f"           THEN class = {rule.target_class}"
                f"  [coverage={rule.coverage*100:.1f}%  confidence={rule.confidence*100:.1f}%]"
            )

    # ── Star algorithm ────────────────────────────────────────────────────────

    def _star(
        self,
        seed: np.ndarray,
        X: np.ndarray,
        y: np.ndarray,
        pos_idx: List[int],
        neg_idx: List[int],
        thresholds: List[List[float]],
        total_pos: int,
    ) -> Optional[Rule]:
        """
        Generate a set of candidate rules that cover *seed* and are
        consistent with the negative examples.  Return the best one.
        """
        # Start with the maximally general rule (no conditions)
        star: List[List[Selector]] = [[]]

        for ni in neg_idx:
            neg_sample = X[ni]

            if not _rule_covers(star[0] if star else [], neg_sample):
                # The current best candidate already excludes this negative
                continue

            new_star: List[List[Selector]] = []

            for candidate_selectors in star:
                # Try extending the candidate with each possible selector
                extensions = self._specialise(
                    candidate_selectors, seed, neg_sample,
                    thresholds
                )
                new_star.extend(extensions)

            # Beam pruning: keep only the top-k candidates by quality
            new_star = self._prune_beam(new_star, X, y, pos_idx, total_pos)

            if new_star:
                star = new_star
            elif star:
                # Existing star is still valid; keep it
                pass
            else:
                return None  # Cannot find any consistent rule

        if not star:
            return None

        # Evaluate all surviving candidates and pick the best
        best_selectors = max(
            star,
            key=lambda s: self._quality(s, X, y, pos_idx, total_pos),
        )
        return self._build_rule(best_selectors, X, y, pos_idx, total_pos)

    def _specialise(
        self,
        current: List[Selector],
        seed: np.ndarray,
        neg: np.ndarray,
        thresholds: List[List[float]],
    ) -> List[List[Selector]]:
        """
        Return all minimal specialisations of *current* that still cover
        *seed* but no longer cover *neg*.
        """
        extensions = []
        for fi, cuts in enumerate(thresholds):
            for cut in cuts:
                for op in (">", "<="):
                    sel = Selector(fi, self.feature_names_[fi], op, cut)
                    # Selector must be satisfied by seed but not by neg
                    if sel.covers(seed) and not sel.covers(neg):
                        # Avoid redundant selectors already in current
                        if not any(
                            s.feature_idx == fi and s.operator == op
                            for s in current
                        ):
                            extensions.append(current + [sel])
        return extensions

    def _prune_beam(
        self,
        candidates: List[List[Selector]],
        X: np.ndarray,
        y: np.ndarray,
        pos_idx: List[int],
        total_pos: int,
    ) -> List[List[Selector]]:
        """Keep only the top beam_width candidates by quality score."""
        if len(candidates) <= self.beam_width:
            return candidates
        scored = [
            (self._quality(c, X, y, pos_idx, total_pos), c)
            for c in candidates
        ]
        scored.sort(key=lambda t: t[0], reverse=True)
        return [c for _, c in scored[: self.beam_width]]

    # ── Evaluation helpers ────────────────────────────────────────────────────

    def _quality(
        self,
        selectors: List[Selector],
        X: np.ndarray,
        y: np.ndarray,
        pos_idx: List[int],
        total_pos: int,
    ) -> float:
        """
        Quality function:
            Q = 0.35 * coverage + 0.65 * confidence
        High weight on confidence prevents noisy/impure rules from being selected.
        Rules with confidence below 0.60 are penalised to near-zero.
        """
        covered_pos = sum(
            1 for i in pos_idx if _rule_covers(selectors, X[i])
        )
        coverage = covered_pos / total_pos if total_pos else 0.0

        all_covered = [i for i in range(len(X)) if _rule_covers(selectors, X[i])]
        if all_covered:
            correct = sum(1 for i in all_covered if y[i] == 1)
            confidence = correct / len(all_covered)
        else:
            confidence = 0.0

        # Hard penalty for impure rules
        if confidence < 0.60:
            return 0.0

        return 0.35 * coverage + 0.65 * confidence

    def _build_rule(
        self,
        selectors: List[Selector],
        X: np.ndarray,
        y: np.ndarray,
        pos_idx: List[int],
        total_pos: int,
    ) -> Rule:
        """Create a Rule object with computed statistics."""
        covered_pos = sum(1 for i in pos_idx if _rule_covers(selectors, X[i]))
        coverage    = covered_pos / total_pos if total_pos else 0.0

        all_covered = [i for i in range(len(X)) if _rule_covers(selectors, X[i])]
        confidence  = (
            sum(1 for i in all_covered if y[i] == 1) / len(all_covered)
            if all_covered else 0.0
        )
        return Rule(
            selectors=selectors,
            target_class=1,
            coverage=coverage,
            confidence=confidence,
            n_covered=covered_pos,
        )

    def _compute_thresholds(self, X: np.ndarray) -> List[List[float]]:
        """
        For each feature, compute a set of candidate cut-points using quantiles.
        """
        thresholds = []
        percentiles = np.linspace(20, 80, self.candidate_thresholds)
        for fi in range(X.shape[1]):
            cuts = np.percentile(X[:, fi], percentiles)
            thresholds.append([round(float(c), 2) for c in np.unique(cuts)])
        return thresholds


# ─── Module-level helpers ────────────────────────────────────────────────────

def _rule_covers(selectors: List[Selector], sample: np.ndarray) -> bool:
    """Return True iff all selectors are satisfied by *sample*."""
    return all(s.covers(sample) for s in selectors)
