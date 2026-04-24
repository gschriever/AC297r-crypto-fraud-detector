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

On the 14 validated tokens (6 FRAUD + 8 non-fraud anomalies), the **continuous
suspicion score at a p90 cutoff catches 100% of known fraud (6/6)** while the
legacy *discrete* 3-vote consensus catches only 17% (1/6). The Layer-2
calibrator cleanly separates the three large non-fraud events (SLP / 3Crv / MIM,
all P(fraud) ≤ 0.15) from rug-like tokens, with the fraud/hack/bug distinction
in the middle band being genuinely hard at this sample size.

| Strategy | Flag rate | Fraud recall (n=6) |
|---|---|---|
| Naive: `volume_spike_ratio > p95` | 5% | 0% |
| Random 5% sample | 5% | 5% |
| Ensemble, ≥2 votes (legacy) | 3.6% | 17% |
| Ensemble, 3 votes (legacy) | 2.3% | 17% |
| **Ensemble, `suspicion_score ≥ p90`** | **10%** | **100%** |

See [artifacts/baseline_comparison.png](artifacts/baseline_comparison.png) for the chart.

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

- The Layer-2 calibrator is fit on **n=14 tokens**. LOO accuracy is ~0.50 at this
  sample size — the reliable story is "we can separate big legitimate events
  from rug-like tokens," not "we know the precise fraud probability of an
  arbitrary flagged token." Expanding the validation set is the most valuable
  single improvement available.
- Token symbols collide on Ethereum (multiple addresses can share a ticker).
  The validation registry is keyed on symbol with case-insensitive lowercase
  matching; ideally it should be re-keyed on `token_address`.
- 37% of tokens (1,588 of 4,334) lack the 24-hour temporal features and are
  imputed with the global median. These tokens still participate in scoring
  but their temporal features should not be over-interpreted.

---

*AC297r Capstone — Gillian Schriever, Jiahui (Cecilia) Cai, Zhilin Chen, Jinghan Huang. Harvard John A. Paulson School of Engineering and Applied Sciences, Spring 2026.*
