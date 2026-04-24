# Master Validation Registry

This is the ground-truth registry that feeds the two-layer unsupervised
pipeline. The canonical machine-readable source is
[validation_registry.csv](validation_registry.csv); this file is its
human-readable companion.

## How the registry is built

Two cohorts, combined and address-keyed (token symbols alone collide on
Ethereum — multiple contracts share the same ticker):

1. **Original hand-curated set (n = 14, source = `manual_registry_v1`).**
   High-profile events the team researched in early April 2026.
2. **Web-researched expansion (n = 55, source = `web_research_2026-04-24`).**
   Stratified sample drawn from the 4,334-token dataset across the full
   suspicion-score range — from quiet (<p50) to 3-vote-consensus — and
   labelled against Etherscan, RugDoc / REKT, CertiK, and major crypto-news
   sources. This cohort was designed to add true negatives (NORMAL tokens)
   which the original registry lacked entirely.

Combined: **69 tokens**, of which **60 are usable labels** (9 tagged
UNKNOWN after research are held out of calibration).

## Taxonomy

- **FRAUD** — Intentional malicious developer intent (rug pull, honeypot,
  phishing drainer, brand impersonation).
- **HACK** — External attack or exploit against an otherwise legitimate
  protocol.
- **BUG** — Technical failure or smart-contract error (not malicious).
- **BENIGN** — Large legitimate anomaly (institutional rebalancing,
  stablecoin peg mechanics, LST/LRT/vault flows).
- **SHOCK** — Market contagion / de-pegging event.
- **NORMAL** — Token with no documented controversial history; operating
  within expected parameters.
- **UNKNOWN** — Insufficient documentation to assign a label; held out.

Only **FRAUD** is treated as a positive by the Layer-2 calibrator.
For Layer-1 (suspicious-behavior detection), the binary question is
`is_anomaly_expected`: all taxonomies except **NORMAL** (and UNKNOWN) are
true anomalies.

## Current distribution

| Taxonomy | HIGH | MEDIUM | LOW | Total |
|---|---:|---:|---:|---:|
| FRAUD   | 6 | 2 | 0 | 8 |
| HACK    | 3 | 0 | 0 | 3 |
| BUG     | 2 | 0 | 0 | 2 |
| BENIGN  | 11 | 0 | 0 | 11 |
| SHOCK   | 1 | 0 | 0 | 1 |
| NORMAL  | 9 | 17 | 9 | 35 |
| UNKNOWN | 0 | 0 | 9 | 9 |

## Performance summary (leave-one-out on n = 60 labeled tokens)

- **LOO accuracy:** 0.883 (was 0.50 on the n = 14 registry)
- **Brier score:** 0.098 (was 0.22)
- **Layer 1 fraud recall** (suspicion_score ≥ p90): **88%** (7 of 8 known frauds)
- **Layer 1 fraud recall** (suspicion_score ≥ p85): **100%** (8 of 8)
- **Layer 1 specificity on NORMAL tokens** (p90 cutoff): 57% — i.e., of 35
  tokens researched as NORMAL, 20 are correctly below p90 and 15 are above.
  The 15 false-flags are concentrated in high-volatility memecoins (WLFI,
  BOSS, DEGEN, TROLL, BIDEN) whose on-chain behavior mimics rug pulls even
  though research confirms them legitimate — this is exactly the failure
  mode Layer 2 (calibration) is designed to catch.

## Headline calibration examples (from artifacts/validated_risk_scores.csv)

| Token | Real label | Votes | Suspicion | P(fraud) LOO | Verdict |
|---|---|:-:|:-:|:-:|---|
| WFT | FRAUD | 3 | 0.98 | **0.95** | Correct — top candidate |
| PLASMA | FRAUD | 0 | 0.91 | **0.78** | Caught by continuous score, flagged correctly |
| YJM | FRAUD | 0 | 0.90 | **0.80** | Same |
| CZI | FRAUD | 0 | 0.88 | **0.61** | Same, lower confidence |
| TETH | BUG | 3 | 1.00 | 0.82 | False positive — Layer 2 can't tell bugs from rugs |
| WLFI | NORMAL | 3 | 1.00 | **0.003** | Correctly dismissed — 3-vote false alarm cleared |
| DEGEN | NORMAL | 3 | 0.99 | **0.04** | Same — meme coin correctly normalized |
| 3Crv | BENIGN | 3 | 0.98 | 0.02 | Correctly low — institutional rebalancing |
| MIM | SHOCK | 3 | 0.98 | 0.02 | Correctly low — de-peg contagion |

## Known limitations

- **Class imbalance.** 8 FRAUD vs. 52 non-FRAUD; the calibrator uses
  `class_weight='balanced'` to compensate, but more FRAUD labels would help.
- **MEDIUM-confidence NORMAL rows.** 17 of the 35 NORMAL tokens are MEDIUM
  confidence — web search found no documented fraud but also no detailed
  legitimacy signal beyond Etherscan holder counts. These could be
  undocumented rugs.
- **TICKER collisions are real.** The registry's `token_address` column is
  the single source of truth. Several tickers (MIM, YANG, TETH, GROK, ZKP,
  VISION, STRAT, TROLL, DEGEN, mUSD) reference multiple distinct projects
  on Ethereum; the registry pins each to one specific contract address.
- **Sample still small.** 60 labeled tokens out of 4,334 is 1.4% of the
  universe. A natural next step is to label 100–200 more using the same
  stratified-sampling + web-research protocol.
