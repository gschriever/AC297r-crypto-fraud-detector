# Supervised pipeline — reference summary

The other half of the AC297r capstone, built by Cecilia Cai, Zhilin
Chen, and Jinghan Huang. This file is a quick-reference summary so the
two pipelines can be compared cleanly on the poster and in future
conversations.

Source materials: `supervised and unsupervised learning comparison/`
(`METHODOLOGY_SUPERVISED.md`, `PHASE_C_SUMMARY.md`, and the three
`*.zip` archives) plus the March 11 mid-semester deck.

---

## Task

**Binary classification of each token: is it a pump-and-dump (P&D)?**

Operational definition of P&D, applied uniformly across all tokens:

  1. **Spike**: price exceeded 2× its trailing 7-day median for at
     least 2 consecutive days, and
  2. **Crash**: ≥80% drop within 60 days of the spike.

Tokens that satisfied both = **positive**; tokens whose price stayed in
a 1.5–5× range over the observation window = **control**; tokens that
spiked but didn't crash = **ambiguous** (held out of training).

This is a *programmatically-derived* label set, not human-validated
fraud taxonomy. So "supervised positive" ≈ "this token's price action
matches the textbook P&D shape," not "this token's developers were
proven malicious."

## Dataset (Phase C, 2026-04-25)

| Stage                                | Count |
|---|---|
| SQL candidates (LIMIT 4000, ratio≥5×) | 4,000 |
| SQL controls (1.5≤ratio<5)            |   620 |
| After dedup                           | 4,033 |
| Passed the spike+crash filter         | 2,283 |
| **Training set**                      | **1,628**  (1,197 positive + 431 control, 2.8 : 1) |
| Ambiguous (spike, no crash)           |   655 |

## Model

- **Random Forest**, stratified 10-fold cross-validation
- Bootstrap 90% CI on each per-token prediction
- (XGBoost optional; falls back to RF if `libomp` missing)

## Headline metrics

| Metric  | Value |
|---|---|
| AUC-ROC | **0.900** |
| AUC-PR  | 0.950 |
| Brier   | 0.114 |
| Bootstrap 90% CI mean width | 0.107 |

## Top-15 features (by importance)

| # | Feature                | Importance |
|---|------------------------|---|
| 1 | token_age_days         | 0.214 |
| 2 | price_max_ratio        | 0.153 |
| 3 | price_volatility       | 0.089 |
| 4 | num_holders            | 0.069 |
| 5 | price_spike_count_10   | 0.058 |
| 6 | price_spike_count_30   | 0.057 |
| 7 | price_spike_count      | 0.056 |
| 8 | price_spike_count_20   | 0.041 |
| 9 | residual_volatility    | 0.036 |
| 10 | wallet_hhi             | 0.036 |
| 11 | residual_max_gain      | 0.028 |
| 12 | conc_top10_pct         | 0.025 |
| 13 | conc_top1_pct          | 0.021 |
| 14 | conc_top5_pct          | 0.020 |
| 15 | residual_max_drawdown  | 0.018 |

Interpretation: *young* tokens with concentrated holders, high pre-
spike volatility, and many spike events are the strongest P&D
predictors. The "residual" features come from a beta normalization
against ETH (Christopher's market-noise removal idea applied
properly at the daily level — supervised side has the daily token
data we lack on the unsupervised side).

## Concordance with the unsupervised pipeline

On the same 1,628-token set:

| Detector           | AUC   |
|--------------------|-------|
| Supervised RF      | 0.900 |
| Isolation Forest   | 0.602 |
| PCA + Mahalanobis  | 0.548 |

Spearman ρ between supervised p̂ and unsupervised score:
- vs Isolation Forest: **0.346**
- vs PCA/Mahalanobis: 0.177

**Low concordance is the most important comparison finding.** The
supervised model learns the specific *price spike + crash* pattern;
the unsupervised pipeline picks up generic statistical anomalies.
The two pipelines find *different* tokens — which is exactly why a
two-pipeline portfolio is more useful than either alone.

## How this relates to our (unsupervised) pipeline

| Dimension | Supervised | Unsupervised (ours) |
|---|---|---|
| Needs labels? | Yes (programmatically derived from price) | No |
| Detects... | Specific P&D *pattern* (spike + crash) | Any unusual token behavior |
| Label source | Algorithmic (price-action criteria) | Hand validation registry (n = 144) |
| Strength | High accuracy on the pattern it was trained on | Catches novel / non-P&D scams (rugs, honeypots, impersonations) |
| Weakness | Misses anomalies that don't follow P&D shape | Lower precision because it flags non-fraud anomalies too (hacks, bugs) |
| Output | P(P&D) + 90% CI | continuous suspicion + P(fraud \| suspicious) |

## Useful poster framing

> The two pipelines answer the same question from opposite ends. The
> supervised model says "*I know what a P&D looks like — does this
> token match?*" — and is very accurate when the answer is yes. The
> unsupervised pipeline says "*I don't assume any specific pattern —
> show me everything that looks weird.*" Together they cover both
> the textbook scams and the novel ones the textbooks haven't caught
> up with yet.
