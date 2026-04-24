# Master Validation Registry

This table records the hand-validated ground-truth labels attached to tokens
that the unsupervised pipeline flagged as suspicious. The registry feeds the
Layer-2 `P(fraud | suspicious)` calibrator in [calibrate.py](calibrate.py).

## Taxonomy

- **FRAUD** — Intentional malicious intent by the token's developers
  (rug pull, honeypot, phishing drainer, brand impersonation).
- **HACK** — External attack or exploit against an otherwise legitimate
  protocol.
- **BUG** — Technical failure or smart-contract error.
- **BENIGN** — Large-scale institutional liquidity movement or rebalancing.
- **SHOCK** — Market contagion / de-pegging event.

Only the **FRAUD** label is treated as a positive by the Layer-2 calibrator;
the four non-fraud categories are all treated as "true anomaly but not fraud."

## The registry (n = 14)

| Token | Real-world event | Taxonomy | Justification |
| :--- | :--- | :---: | :--- |
| TETH | Decimal-precision failure | **BUG** | Math error in contract triggered mass liquidations. |
| SLP | $622M Ronin Hack | **HACK** | Caught massive capital panic flight. |
| 3Crv | Curve 3pool rebalancing | **BENIGN** | Institutional whale swaps between DAI/USDC. |
| plasma | Wallet-drainer phishing | **FRAUD** | Fraudulent contract designed to steal assets. |
| CZI | Binance impersonator | **FRAUD** | Brand hijacking targeting the Binance CEO name. |
| VAL | Insider "soft rug" | **FRAUD** | Developer/insider dump at liquidity peak. |
| GREED | High-cap rug pull | **FRAUD** | Project abandoned after $100M+ volume anomaly. |
| MIM | UST contagion | **SHOCK** | Algorithmic stablecoin de-pegging exit event. |
| YANG | Defrost Finance hack | **HACK** | Compromised admin key (social-engineering). |
| WFT | Low-cap rug pull | **FRAUD** | Smaller anonymous exit scam. |
| apxUSD | Stablecoin liquidity | **BENIGN** | Oversupply rebalancing in Apyx Finance. |
| YJM | Dusting scam | **FRAUD** | Malicious token sent unsolicited to drain wallets. |
| rstETH | Mellow staking volatility | **BENIGN** | High-volume restaking vault mechanics. |
| hemiBTC | Hemi vault receipt | **BENIGN** | Legitimate vault balancing of BTC receipt tokens. |

**Distribution:** 6 FRAUD, 3 BENIGN, 2 HACK, 1 BUG, 1 SHOCK, 1 BENIGN (stablecoin).

## Model performance on the validated subset

See [artifacts/validated_risk_scores.csv](artifacts/validated_risk_scores.csv)
for the full table including Layer-1 suspicion score and Layer-2 leave-one-out
P(fraud) for each of the 14 tokens.

**Layer 1 (continuous suspicion score, p90 cutoff):**
- True positives (fraud caught): 6 — WFT, GREED, VAL, PLASMA, YJM, CZI
- False negatives (fraud missed): 0
- "False positives" that are actually desirable catches: 8 — all of the non-fraud
  anomalies also land in the flagged set, which is Layer 1's job. Layer 2 is
  what separates fraud from non-fraud anomaly.

**Layer 2 (P(fraud) calibration, leave-one-out):**
- LOO accuracy: ~0.50 on n=14 — small-sample noisy.
- Strong separation at the tails: SLP / 3Crv / MIM all score P(fraud) ≤ 0.15.
- Middle band is genuinely hard: 5 of 6 frauds live between P = 0.45 and 0.73,
  alongside YANG (HACK), TETH (BUG), apxUSD / hemiBTC (BENIGN).

## Known limitations of this registry

- **Small sample size (n=14).** The single largest available improvement is
  hand-labeling more flagged tokens from `artifacts/top_fraud_candidates.csv`.
- **Keyed on symbol, not address.** Token symbols collide on Ethereum (multiple
  contract addresses share tickers like "MIM", "YANG", "TETH"). The pipeline
  handles this with case-insensitive lowercase matching + dedup on the
  most-anomalous candidate per symbol, but the authoritative fix is to add
  `token_address` to each registry row.
