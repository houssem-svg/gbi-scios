"""Monte Carlo win-probability simulation.

Per the engineering spec (💡.docx Microservice 3, line 921-964):

    P(Win) = (1/N) × Σ I(Score_Client > Score_Competitor^(i))

The competitor's bid and LC score are sampled from normal distributions
(mean and std provided by the caller) over N iterations (default 10,000).
For each iteration, the competitor's score is computed using the same
scoring formula as the client (60/40, 70/30, ...) and compared to the
client's known score.

Uses numpy for vectorized sampling (10K iterations in ~5ms).
Falls back to a pure-Python loop if numpy is unavailable.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

from app.core.config import settings


@dataclass(frozen=True)
class MonteCarloInput:
    client_score: float
    competitor_bid_mean: float
    competitor_bid_std: float
    competitor_lc_mean: float
    competitor_lc_std: float
    # The winning bid value used as P_min in the competitor score calc.
    # Typically the client's own bid (or the lowest known bid).
    p_min: float
    # Scoring weights (lc_weight, price_weight) — pass the resolved weights
    # for the active formula. Defaults to 60/40 per the spec.
    lc_weight: float = 40.0
    price_weight: float = 60.0
    iterations: int = 10_000
    # Optional Tadawul bonus added to the competitor's final score.
    competitor_tadawul_bonus: float = 0.0


@dataclass(frozen=True)
class MonteCarloResult:
    win_probability: float  # 0.0 – 100.0 (percentage)
    iterations: int
    client_score: float
    competitor_score_mean: float
    competitor_score_std: float


def _score(p_eval: float, p_min: float, lc: float, lc_weight: float, price_weight: float) -> float:
    """Spec scoring formula: (P_min/P_eval × price_weight) + (LC × lc_weight/100)."""
    if p_eval <= 0:
        return 0.0
    price_score = (p_min / p_eval) * 100.0
    return (price_weight / 100.0) * price_score + (lc_weight / 100.0) * lc


def run_monte_carlo(data: MonteCarloInput) -> MonteCarloResult:
    """Run the simulation and return the win probability (%)."""
    if data.iterations <= 0:
        return MonteCarloResult(
            win_probability=0.0,
            iterations=0,
            client_score=data.client_score,
            competitor_score_mean=0.0,
            competitor_score_std=0.0,
        )

    try:
        import numpy as np  # type: ignore[import-untyped]

        comp_bids = np.random.normal(
            data.competitor_bid_mean, data.competitor_bid_std, data.iterations
        )
        comp_lcs = np.random.normal(
            data.competitor_lc_mean, data.competitor_lc_std, data.iterations
        )
        # Clamp LC to [0, 100]; clamp bids to >= 1 to avoid div-by-zero.
        comp_lcs = np.clip(comp_lcs, 0.0, 100.0)
        comp_bids = np.maximum(comp_bids, 1.0)

        # Vectorized scoring.
        price_scores = (data.p_min / comp_bids) * 100.0
        comp_scores = (
            (data.price_weight / 100.0) * price_scores
            + (data.lc_weight / 100.0) * comp_lcs
            + data.competitor_tadawul_bonus
        )

        wins = int(np.sum(data.client_score > comp_scores))
        win_prob = (wins / data.iterations) * 100.0
        return MonteCarloResult(
            win_probability=round(win_prob, 2),
            iterations=data.iterations,
            client_score=data.client_score,
            competitor_score_mean=float(np.mean(comp_scores)),
            competitor_score_std=float(np.std(comp_scores)),
        )
    except ImportError:
        # numpy not installed — fall back to pure Python (slower but correct).
        return _run_monte_carlo_pure(data)


def _run_monte_carlo_pure(data: MonteCarloInput) -> MonteCarloResult:
    rng = random.Random()
    wins = 0
    comp_scores: list[float] = []
    for _ in range(data.iterations):
        bid = max(
            1.0,
            rng.gauss(data.competitor_bid_mean, data.competitor_bid_std),
        )
        lc = max(0.0, min(100.0, rng.gauss(data.competitor_lc_mean, data.competitor_lc_std)))
        score = _score(bid, data.p_min, lc, data.lc_weight, data.price_weight) + data.competitor_tadawul_bonus
        comp_scores.append(score)
        if data.client_score > score:
            wins += 1

    mean = sum(comp_scores) / len(comp_scores) if comp_scores else 0.0
    variance = sum((s - mean) ** 2 for s in comp_scores) / len(comp_scores) if comp_scores else 0.0
    std = math.sqrt(variance)
    return MonteCarloResult(
        win_probability=round((wins / data.iterations) * 100.0, 2),
        iterations=data.iterations,
        client_score=data.client_score,
        competitor_score_mean=mean,
        competitor_score_std=std,
    )
