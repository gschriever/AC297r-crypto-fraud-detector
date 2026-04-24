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
```

All four scripts write to `./artifacts/`. `pipeline.py` is the entry point and
produces the canonical `tokens_scored.csv` that every downstream script reads.

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
