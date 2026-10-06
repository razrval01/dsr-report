# Deflated Sharpe Ratio (DSR)

**Separating genuine trading skill from backtest luck.**

> A high backtested Sharpe ratio is one of the most commonly misread numbers in quantitative finance. The more strategy variants you try, the higher a Sharpe ratio pure chance alone will hand you. This repo implements the Deflated Sharpe Ratio (Bailey & López de Prado, 2014) — a correction that accounts for the number of trials, sample length, and non-normal returns — plus a working demo that reproduces the selection-bias effect from scratch.

📄 **[Read the full write-up →](REPORT.md)**

-----

## Why this exists

Run a thousand zero-edge, purely random strategies over a year of data and report only the best one, and you’ll see Sharpe ratios north of 2.0 — not because any of them work, but because you looked a thousand times. The Deflated Sharpe Ratio turns a reported Sharpe into a statistically honest number: the probability that a true edge exists at all, once the search that produced it is accounted for.

## What’s in this repo

|File                                              |Description                                                                                                                                          |
|--------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------|
|[`REPORT.md`](REPORT.md)                          |Full methodology write-up: the selection-bias problem, the DSR derivation, and a three-layer validation protocol (DSR + out-of-sample + Monte Carlo).|
|[`src/deflated_sharpe.py`](src/deflated_sharpe.py)|Reference implementation: `sharpe_standard_error`, `expected_max_sharpe`, `deflated_sharpe_ratio`, plus runnable demos.                              |

## Quick start

```bash
git clone https://github.com/razrval01/deflated-sharpe-ratio.git
cd deflated-sharpe-ratio
pip install -r requirements.txt
python src/deflated_sharpe.py
```

This runs three demos:

1. **Selection bias in action** — simulates up to 100,000 independent, zero-edge strategies and shows the *best* observed Sharpe climbing steadily with the number of trials, even though none of them have any real edge.
1. **DSR evaluation** — compares a “found” strategy from a 500-variant search against the deflated luck benchmark, once with no real edge (correctly flagged as indistinguishable from luck) and once with a genuine edge (correctly flagged as likely real).
1. **Monte Carlo reshuffle** — bootstraps a return sequence to show where the realized equity curve sits within the distribution of outcomes the same trades could have produced in a different order.

## Using it on your own strategy

```python
from src.deflated_sharpe import expected_max_sharpe, deflated_sharpe_ratio

# Your search parameters
n_trials = 240          # how many configurations you actually tried
observed_sharpe = 1.85  # the Sharpe of the one you're reporting
T = 504                 # number of return periods (e.g. trading days)
sigma_sharpe = 0.6      # std. dev. of Sharpe ratios across your trials

sr0 = expected_max_sharpe(sigma_sharpe, n_trials)
dsr = deflated_sharpe_ratio(observed_sharpe, sr0, T, returns=my_return_series)

print(f"Deflated Sharpe Ratio: {dsr:.3f}")
```

**Be honest about `n_trials`.** The number you must disclose isn’t just the Sharpe ratio of the winner — it’s how many configurations you tried to find it. Undercounting trials is the single easiest way to fool yourself (or others) with this test.

## Methodology

Formulas follow:

- Bailey, D. H., & López de Prado, M. (2014). *The Deflated Sharpe Ratio: Correcting for Selection Bias, Backtest Overfitting and Non-Normality.* Journal of Portfolio Management, 40(5).
- Lo, A. (2002). *The Statistics of Sharpe Ratios.* Financial Analysts Journal, 58(4).

Full derivation and intuition in [`REPORT.md`](REPORT.md).

## Disclaimer

This is an educational reference implementation, not investment advice. DSR tells you whether an observed Sharpe ratio is statistically distinguishable from the luck you’d expect given your search — it does not guarantee future performance, and should be used alongside out-of-sample testing and Monte Carlo validation, not as a standalone pass/fail gate.

## License

MIT

-----

*Part of an ongoing series on quantitative research methodology — see also: [DeFi Research Report — Aave V3/V4](https://github.com/razrval01/defi-report).*