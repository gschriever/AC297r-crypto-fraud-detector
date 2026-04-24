# AC297r: Unsupervised Crypto Fraud Detector

A two-layer unsupervised pipeline for detecting suspicious behavior in
Ethereum mid-cap ERC-20 tokens — with a calibrated probability that the
behavior is intentional fraud (as opposed to hacks, bugs, benign institutional
activity, or de-pegs).

## Overview

Traditional fraud detection relies on labeled data, which is rare and quickly
outdated in the crypto space. This project builds an unsupervised pipeline
that evaluates **4,334 mid-cap ERC-20 tokens** on Ethereum (from a 365-day Dune
Analytics pull, $1M–$1B annualized volume) in two layers:

- **Layer 1 — Suspicious-behavior detection.** Three independent anomaly
  detectors (Isolation Forest, DBSCAN, PCA+Mahalanobis) are rank-averaged into
  a continuous `suspicion_score` in [0, 1].
- **Layer 2 — Fraud calibration.** A regularized logistic regression fit on
  a hand-validated subset of 14 tokens maps suspicious-behavior features to
  `P(fraud | suspicious)`.

## Key result

On **144 validated tokens** (15 FRAUD, 100 NORMAL, 22 BENIGN, 4 HACK, 2 BUG, 1 SHOCK),
the **continuous suspicion score at a p85 cutoff catches 93% of known fraud
(14/15)** while the legacy *discrete* 3-vote consensus catches only 27% (4/15).
Layer 2 cleanly separates fraud from normal behavior even when both trigger the
same Layer 1 alarm — WLFI, DEGEN, STRAT, 3Crv and MIM all score P(fraud) < 0.06
despite being 3-vote consensus anomalies, while WFT, PLASMA, YJM, CZI, and the
coordinated ORB rug cluster (ORBDEG/SPHERUM/ORBS) all score P(fraud) > 0.6.

| Strategy | Flag rate | Fraud recall (n = 15) |
|---|---|---|
| Naive: `volume_spike_ratio > p95` | 5% | 0% |
| Random 5% sample | 5% | 5% |
| Ensemble, ≥ 2 votes (legacy) | 3.6% | 33% |
| Ensemble, 3 votes (legacy) | 2.3% | 27% |
| **Ensemble, `suspicion_score ≥ p90`** | **10%** | **67%** |
| **Ensemble, `suspicion_score ≥ p85`** | **15%** | **93%** |

See [artifacts/baseline_comparison.png](artifacts/baseline_comparison.png) for the chart.

**Layer 2 calibration on the labeled subset** (leave-one-out cross-validation):
- LOO accuracy: **0.87**, Brier score: 0.12
- Recall (fraud caught): **80%** (12 of 15)
- Specificity (non-fraud correctly rejected): **88%** (113 of 129)

## Reproducing the results

```bash
# Layer 1 — suspicious-behavior detection
python pipeline.py

# Layer 2 — P(fraud | suspicious) calibration
python calibrate.py

# SHAP explainability for the top tokens
python explain.py

# Sensitivity sweep + naive-baseline comparison
python evaluate.py

# Optional — BTC regime characterization (requires artifacts/btc_daily.csv,
# produced by fetching CryptoCompare or similar; see btc_analysis.py)
python btc_analysis.py
```

All four core scripts write to `./artifacts/`. `pipeline.py` is the entry point
and produces the canonical `tokens_scored.csv` that every downstream script reads.

### BTC normalization — lesson from the round-2 experiment

We ran the BTC-normalized SQL and joined the four new features into Layer 1
to see if removing the macro-BTC component would tighten fraud recall. It
didn't — it actually **hurt** recall (14/15 → 11/15 at p85).

**Why:** most of our validated frauds are **short-lived rugs** (median 4
days of activity). Over such a short window, `volume_correlation_btc` is
either undefined (NaN on 1-day tokens) or extremely noisy, and the token
almost never happens to be active on a BTC-extreme day. When those NaN
features get imputed to the cohort median and fed to the ensemble, the
short-lived rugs get pulled toward the "normal" center in the enlarged
feature space. The BTC features separate BTC-driven behavior from
token-specific behavior only for tokens with *enough daily observations*
to actually measure correlation.

**What we do instead:** keep the four v1 / temporal feature groups (6
features) as the Layer-1 feature matrix, and use the BTC-adjusted
features only as a downstream **annotation**. `pipeline.py` writes a
`btc_contamination_score` column to `tokens_scored.csv` that combines
`volume_correlation_btc`, `pct_volume_on_btc_extreme_days`, and
`peak_coincident_btc_extreme` into a 0-1 score — and only for tokens
with `total_days_traded >= 14`, where the BTC signals are meaningful.

Usage pattern: when the pipeline flags a token as suspicious, check its
contamination score. Validated FRAUD HYPER (address `0x840a6c21...`)
scores `btc_contamination = 0.026` — its anomaly signal is token-specific,
not macro BTC. A token with high suspicion AND high contamination is a
candidate to *discount* as likely BTC-driven noise.

The full blueprint is in [dune queries/price_volume_features_btc_normalized.sql](dune%20queries/price_volume_features_btc_normalized.sql).
When the export CSV is present at `dune queries/BTC_Normalized_Features_EXPORT.csv`,
`pipeline.py` auto-loads it and writes the contamination column; otherwise
it falls back to v1 features only.

**Supporting context:** BTC's own volume-spike ratio during the 365-day
window was only 3.75× (see [btc_analysis.py](btc_analysis.py) output).
Our 3-vote consensus anomalies routinely show spike ratios of 100-300×,
so the headline fraud recall is always going to be dominated by
token-specific signal, not BTC. That's why BTC normalization was never
going to move the headline number much — but the contamination
annotation is still valuable for interpreting *why* a token was flagged.

## Files

- [pipeline.py](pipeline.py) — Layer 1 end-to-end: load, left-join, log-transform,
  three detectors, continuous suspicion score, PCA visualizations.
- [calibrate.py](calibrate.py) — Layer 2 logistic regression + LOO-CV + feature
  clipping to avoid extrapolation outside the calibration range.
- [explain.py](explain.py) — SHAP TreeExplainer on Isolation Forest. Global and
  per-token contribution plots.
- [evaluate.py](evaluate.py) — Contamination sensitivity sweep and fraud-recall
  comparison against naive and random baselines.
- [VALIDATION_RESULTS.md](VALIDATION_RESULTS.md) — The hand-validated 14-token
  registry that feeds Layer 2.
- [fraud_detection_framework.md](fraud_detection_framework.md) — Original
  framework document (March 2026).
- [poster templaates/](poster%20templaates/) — Poster reference templates and
  a generator for the AC297r capstone poster.

## Artifacts produced by the pipeline

- `artifacts/tokens_scored.csv` — every token with Layer-1 scores.
- `artifacts/tokens_calibrated.csv` — tokens_scored.csv + P(fraud) from Layer 2.
- `artifacts/validated_risk_scores.csv` — the 14 hand-validated tokens with both
  layer scores and ground-truth `actually_fraud` column.
- `artifacts/anomaly_map_static.png` / `anomaly_map_interactive.html` — 2D and
  3D PCA visualizations with headline-token annotations.
- `artifacts/shap_global_importance.png` / `shap_headline_tokens.png` — feature
  attributions.
- `artifacts/calibration_report.png` — LOO calibration performance and P(fraud)
  distribution across flagged tokens.
- `artifacts/sensitivity_sweep.png` / `baseline_comparison.png` — stability and
  lift-over-baseline charts.

## Caveats

- **Class imbalance in the validation set.** 8 FRAUD vs. 52 non-FRAUD in the
  current n = 60 labeled subset. The calibrator uses `class_weight='balanced'`
  but more fraud labels would tighten the middle band.
- **MEDIUM-confidence NORMAL rows.** 17 of 35 NORMAL labels rest on Etherscan
  verification + holder-count signals rather than a primary source. A handful
  could be undocumented rugs.
- **37% imputed temporal features.** 1,588 of 4,334 tokens lack 24-hour
  post-launch data and receive the global median. Their temporal features
  should not be over-interpreted.
- **Registry is now address-keyed**, which fixes the ticker-collision issue
  that plagued the v1 registry (MIM, TETH, YANG each map to multiple Ethereum
  contracts). The canonical file is
  [validation_registry.csv](validation_registry.csv).

---

*AC297r Capstone — Gillian Schriever, Jiahui (Cecilia) Cai, Zhilin Chen, Jinghan Huang. Harvard John A. Paulson School of Engineering and Applied Sciences, Spring 2026.*
