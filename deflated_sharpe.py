"""
Deflated Sharpe Ratio (DSR) — reference implementation
Methodology: Bailey & Lopez de Prado (2014); SE(Sharpe) after Lo (2002)

This module:
  1. Computes the standard error of an estimated Sharpe ratio (Lo, 2002).
  2. Computes the expected maximum Sharpe ratio across N independent,
     zero-edge trials (selection bias benchmark).
  3. Computes the Deflated Sharpe Ratio (DSR) for an observed strategy.
  4. Demonstrates selection bias empirically with simulated zero-edge
     strategies.
  5. Runs a simple Monte Carlo trade-reshuffle for equity curve robustness.

Usage:
    python deflated_sharpe.py
"""

from __future__ import annotations
import numpy as np
from scipy.stats import norm, skew, kurtosis

EULER_MASCHERONI = 0.5772156649015329


def sharpe_standard_error(sharpe_hat: float, T: int) -> float:
    """
    Approximate standard error of an estimated Sharpe ratio (Lo, 2002).

    Parameters
    ----------
    sharpe_hat : observed (annualized) Sharpe ratio
    T          : number of years (or return periods) in the sample

    Returns
    -------
    Standard error of the Sharpe estimate.
    """
    return np.sqrt((1 + 0.5 * sharpe_hat ** 2) / T)


def expected_max_sharpe(sigma_sharpe: float, n_trials: int) -> float:
    """
    Expected maximum Sharpe ratio across `n_trials` independent,
    zero-true-Sharpe strategies (the "deflated benchmark" building block).

    Parameters
    ----------
    sigma_sharpe : cross-sectional std. dev. of Sharpe ratios across trials
    n_trials     : number of independent strategy variants tried

    Returns
    -------
    Expected value of the maximum observed Sharpe ratio under pure luck.
    """
    if n_trials <= 1:
        return 0.0
    gamma = EULER_MASCHERONI
    term1 = (1 - gamma) * norm.ppf(1 - 1 / n_trials)
    term2 = gamma * norm.ppf(1 - 1 / (n_trials * np.e))
    return sigma_sharpe * (term1 + term2)


def deflated_sharpe_ratio(
    sharpe_hat: float,
    sharpe_benchmark: float,
    T: int,
    returns: np.ndarray | None = None,
) -> float:
    """
    Compute the Deflated Sharpe Ratio: the probability that the true
    Sharpe ratio exceeds zero, after correcting for the number of trials
    (via `sharpe_benchmark`), sample length, and non-normality of returns.

    Parameters
    ----------
    sharpe_hat       : observed Sharpe ratio of the selected strategy
    sharpe_benchmark : expected max Sharpe from luck alone (SR_0), see
                        `expected_max_sharpe`
    T                : number of return periods in the sample
    returns          : optional return series used to estimate skewness
                        and kurtosis; if omitted, a normal distribution
                        is assumed (skew=0, excess kurtosis=0)

    Returns
    -------
    DSR in [0, 1]. Values near 1.0 indicate the edge survives correction;
    values near 0.5 or below indicate the Sharpe is statistically
    indistinguishable from luck.
    """
    if returns is not None and len(returns) > 2:
        gamma3 = skew(returns)
        gamma4 = kurtosis(returns, fisher=False)  # non-excess kurtosis
    else:
        gamma3, gamma4 = 0.0, 3.0

    numerator = (sharpe_hat - sharpe_benchmark) * np.sqrt(T - 1)
    denom_inner = 1 - gamma3 * sharpe_hat + ((gamma4 - 1) / 4) * sharpe_hat ** 2
    denom_inner = max(denom_inner, 1e-8)  # guard against negative/zero
    denominator = np.sqrt(denom_inner)

    return float(norm.cdf(numerator / denominator))


# ---------------------------------------------------------------------------
# Demo 1: selection bias in action
# ---------------------------------------------------------------------------
def demo_selection_bias(n_trials_list=(1, 10, 100, 1_000, 10_000, 100_000), T=252, seed=42):
    """
    Simulate `max(n_trials_list)` independent, zero-edge daily return series
    over T periods, and show how the BEST observed annualized Sharpe among
    the first n trials grows purely from search -- with no real edge
    anywhere in the data.
    """
    rng = np.random.default_rng(seed)
    max_n = max(n_trials_list)

    # Simulate max_n independent strategies, each T daily returns, zero true edge
    daily_returns = rng.normal(loc=0.0, scale=0.01, size=(max_n, T))
    sharpes = (daily_returns.mean(axis=1) / daily_returns.std(axis=1)) * np.sqrt(252)

    print("Selection bias demo: best Sharpe among N zero-edge strategies")
    print(f"{'N trials':>10} | {'Best observed Sharpe':>22} | {'Theoretical E[max]':>20}")
    print("-" * 60)
    for n in n_trials_list:
        best_sharpe = sharpes[:n].max()
        sigma = sharpes[:n].std()
        theoretical = expected_max_sharpe(sigma, n)
        print(f"{n:>10} | {best_sharpe:>22.3f} | {theoretical:>20.3f}")
    print()


# ---------------------------------------------------------------------------
# Demo 2: DSR applied to a "found" strategy
# ---------------------------------------------------------------------------
def demo_dsr_evaluation(n_trials=500, T=252, true_edge_sharpe=0.0, seed=7):
    """
    Simulate `n_trials` strategies (optionally with a small true edge in one
    of them) and evaluate the DSR of the winning strategy.
    """
    rng = np.random.default_rng(seed)
    daily_returns = rng.normal(loc=0.0, scale=0.01, size=(n_trials, T))

    # Optionally inject a genuine (small) edge into one strategy
    if true_edge_sharpe > 0:
        edge_daily_mean = true_edge_sharpe * 0.01 / np.sqrt(252)
        daily_returns[0] += edge_daily_mean

    sharpes = (daily_returns.mean(axis=1) / daily_returns.std(axis=1)) * np.sqrt(252)
    winner_idx = sharpes.argmax()
    winner_sharpe = sharpes[winner_idx]
    winner_returns = daily_returns[winner_idx]

    sigma_sharpe = sharpes.std()
    sr0 = expected_max_sharpe(sigma_sharpe, n_trials)
    dsr = deflated_sharpe_ratio(winner_sharpe, sr0, T, returns=winner_returns)

    print("DSR evaluation of the best strategy found among a search")
    print(f"  Trials searched:        {n_trials}")
    print(f"  True edge injected:     {'yes' if true_edge_sharpe > 0 else 'no'}")
    print(f"  Winning Sharpe (raw):   {winner_sharpe:.3f}")
    print(f"  Luck benchmark (SR_0):  {sr0:.3f}")
    print(f"  Deflated Sharpe Ratio:  {dsr:.3f}")
    verdict = "likely genuine edge" if dsr > 0.95 else "indistinguishable from luck" if dsr < 0.6 else "inconclusive"
    print(f"  Verdict:                {verdict}")
    print()


# ---------------------------------------------------------------------------
# Demo 3: Monte Carlo trade-reshuffle robustness check
# ---------------------------------------------------------------------------
def demo_monte_carlo_reshuffle(returns: np.ndarray, n_sims=5_000, seed=1):
    """
    Bootstrap-reshuffle a realized trade/return sequence to build a
    distribution of possible terminal outcomes, and report where the
    realized (in-order) outcome sits within that distribution.
    """
    rng = np.random.default_rng(seed)
    realized_terminal = np.prod(1 + returns) - 1

    sim_terminals = np.empty(n_sims)
    for i in range(n_sims):
        shuffled = rng.permutation(returns)
        sim_terminals[i] = np.prod(1 + shuffled) - 1

    percentile = (sim_terminals < realized_terminal).mean() * 100

    print("Monte Carlo trade-reshuffle check")
    print(f"  Realized terminal return:   {realized_terminal:.2%}")
    print(f"  Simulated mean (shuffled):  {sim_terminals.mean():.2%}")
    print(f"  Simulated 5th/95th pct:     {np.percentile(sim_terminals,5):.2%} / {np.percentile(sim_terminals,95):.2%}")
    print(f"  Realized result percentile: {percentile:.1f}th")
    print()


if __name__ == "__main__":
    demo_selection_bias()
    # Pure luck case: 500 zero-edge trials, best one is pure noise
    demo_dsr_evaluation(n_trials=500, true_edge_sharpe=0.0, T=252)
    # Genuine edge case: a real (if modest) edge, measured over a longer
    # sample so it has a chance to show up above the noise floor
    demo_dsr_evaluation(n_trials=500, true_edge_sharpe=3.0, T=1260)

    rng = np.random.default_rng(3)
    sample_returns = rng.normal(0.0006, 0.009, 252)
    demo_monte_carlo_reshuffle(sample_returns)
