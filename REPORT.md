# The Deflated Sharpe Ratio: Separating Genuine Skill from Backtest Luck

**Systematic Strategy Research — Working Paper**
*Methodology after Bailey & López de Prado (2014); standard error after Lo (2002)*

-----

## Abstract

A high backtested Sharpe ratio is one of the most commonly misread numbers in quantitative finance. The moment a researcher tries many strategy variants — different lookbacks, thresholds, universes, holding periods — and reports only the best result, that result stops being a measurement of skill and becomes a measurement of how much search was performed. This report walks through the Deflated Sharpe Ratio (DSR): why naive Sharpe ratios get inflated by multiple testing, how DSR corrects for the number of trials, sample length, and non-normal returns, and how to fold it into a practical validation workflow alongside out-of-sample testing and Monte Carlo resampling.

-----

## 1. The Problem: Selection Bias in Backtesting

A backtest is, by construction, a report of performance on data that has already happened. The danger isn’t backtesting itself — it’s *how many* backtests were run before one was chosen. Varying lookback windows, entry/exit thresholds, asset universes, and holding periods across dozens or hundreds of configurations, then presenting only the winner, is a form of multiple hypothesis testing. Even a completely random, skill-free strategy will occasionally produce an eye-catching Sharpe ratio purely because enough variants were tried. The reported number reflects the size of the search, not the quality of the idea.

## 2. The Arithmetic of Getting Fooled

Assume a strategy has a true Sharpe ratio of zero and is estimated over *T* years of data. Lo (2002) shows that the annualized Sharpe estimate has an approximate standard error of:

```
SE(Ŝharpe) ≈ sqrt( (1 + Ŝharpe²/2) / T )
```

For a true Sharpe of zero and one year of data, this standard error is close to 1.0 — meaning a skill-less strategy’s measured Sharpe behaves roughly like a draw from a standard normal distribution. Now take the *best* of N independent, equally skill-less strategies. The expected maximum of that search grows with N:

```
E[max(Ŝharpe_i)] ≈ σ · sqrt(2 · ln N)
```

The consequence is uncomfortable: search enough noise and an impressive Sharpe ratio appears for free. Run one million zero-edge variants over a single year of data and the best of them is expected to show a Sharpe near 1.7 — not because the strategy works, but purely because of how many were tried.

## 3. The Deflated Sharpe Ratio

Bailey & López de Prado (2014) turn this arithmetic into a formal test. The first step is defining a **deflated benchmark** — the Sharpe ratio one should *expect from luck alone*, given N trials:

```
SR_0 = σ(Ŝharpe) · [ (1-γ)·Φ⁻¹(1-1/N) + γ·Φ⁻¹(1-1/(N·e⁻¹)) ]
```

where σ(Ŝharpe) is the dispersion of Sharpe ratios across trials, γ is the Euler–Mascheroni constant, and Φ⁻¹ is the inverse standard normal CDF.

The Deflated Sharpe Ratio is then the probability that the *true* Sharpe exceeds zero, once the observed Sharpe is measured against this inflated benchmark and adjusted for the skew and kurtosis of the return stream:

```
DSR = Φ( [ (Ŝharpe - SR_0)·sqrt(T-1) ] / sqrt(1 - γ₃·Ŝharpe + ((γ₄-1)/4)·Ŝharpe²) )
```

γ₃ and γ₄ are the skewness and excess kurtosis of the returns. Both terms under the square root penalize the negatively-skewed, fat-tailed return profile typical of strategies that look smooth right up until they don’t (short-volatility, option-selling, and many market-making strategies fall into this bucket). A DSR near 1.0 means the edge survives correction for the search that produced it. A DSR near 0.5 or below means the headline Sharpe is statistically indistinguishable from luck.

## 4. Why It Matters

The inputs carry the intuition directly:

- **More trials (N) → higher bar.** The more configurations tried, the higher the Sharpe must be to clear the luck benchmark.
- **Shorter sample (T) → less confidence.** A high Sharpe over a short window carries more uncertainty than the same Sharpe over a long one.
- **A single, clean test beats a tuned ensemble.** One honest test at a modest Sharpe can outperform, in evidentiary value, the best result of a hundred tuned runs at a nominally higher one.

The number that matters isn’t just the Sharpe ratio reported — it’s the Sharpe ratio *together with* how many configurations were tried to find it. A Sharpe of 2.0 from the first and only backtest run is a very different claim from a Sharpe of 2.0 that was the best of 500 variants.

## 5. A Practical Validation Protocol

DSR is a necessary check, but not a sufficient one on its own. In practice, it belongs inside a three-layer audit:

**(i) Deflated Sharpe.** Correct the reported Sharpe for the number of variants tried, the sample length, and the non-normality of returns.

**(ii) Out-of-sample testing.** Split the history into a development window and a holdout the strategy never saw during tuning. A genuine edge tends to survive the holdout; an overfit one typically collapses.

**(iii) Monte Carlo resampling.** Bootstrap and reshuffle the trade sequence to build a distribution of possible equity curves. This reveals how fragile the realized curve actually is, and where the observed result sits within the full distribution of outcomes the strategy could plausibly have produced.

A strategy that clears all three layers isn’t guaranteed to be profitable going forward — markets change, regimes shift, costs evolve. But it is no longer merely the luckiest draw from a large, unreported search. That distinction — a genuine, if modest, edge versus an expensive illusion — is the entire point of the exercise.

## 6. Worked Example

See [`src/deflated_sharpe.py`](src/deflated_sharpe.py) for a working implementation. The script:

1. Simulates N independent, zero-edge strategies over a configurable sample length.
1. Shows how the *best* observed Sharpe among them grows with N, purely from selection — reproducing the `E[max(Ŝharpe)] ≈ σ·sqrt(2·ln N)` relationship empirically.
1. Computes the Deflated Sharpe Ratio for a given strategy, correcting for N, T, skewness, and kurtosis.
1. Runs a basic Monte Carlo trade-reshuffle to show the dispersion of possible outcomes around a realized equity curve.

Run it with:

```bash
python src/deflated_sharpe.py
```

## References

- Bailey, D. H., & López de Prado, M. (2014). *The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting, and Non-Normality.* Journal of Portfolio Management, 40(5).
- Lo, A. (2002). *The Statistics of Sharpe Ratios.* Financial Analysts Journal, 58(4).

-----

*This document is an educational reference summarizing established academic methodology. It is not investment advice.*