# Master Validation Registry

This is the ground-truth registry that feeds the two-layer unsupervised
pipeline. The canonical machine-readable source is
[validation_registry.csv](validation_registry.csv); this file is its
human-readable companion.

## How the registry is built

Three cohorts, combined and address-keyed (token symbols alone collide on
Ethereum — multiple contracts share the same ticker):

1. **Original hand-curated set (n = 14, source = `manual_registry_v1`).**
   High-profile events the team researched in early April 2026.
2. **Round 1 web research (n = 55, source = `web_research_2026-04-24`).**
   Stratified sample across the full suspicion-score range, designed to
   add true negatives (NORMAL tokens) which the original registry
   entirely lacked.
3. **Round 2 web research (n = 100, source = `web_research_2026-04-24_round2`).**
   A larger sample weighted toward the gaps — more rug-pattern candidates
   (short lifespan + high trade dominance), more high-volume 3-vote
   consensus tokens, and more quiet-stratum NORMALs to stabilize the
   specificity estimate.

Combined: **169 tokens**, of which **144 are usable labels** (25 tagged
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
| FRAUD   | 7  | 8  | 0  | 15  |
| HACK    | 4  | 0  | 0  | 4   |
| BUG     | 2  | 0  | 0  | 2   |
| BENIGN  | 22 | 0  | 0  | 22  |
| SHOCK   | 1  | 0  | 0  | 1   |
| NORMAL  | 26 | 42 | 32 | 100 |
| UNKNOWN | 0  | 0  | 25 | 25  |

## Performance summary (leave-one-out on n = 144 labeled tokens)

- **LOO accuracy:** 0.868 (stable vs. 0.883 on n = 60, 0.50 on n = 14 — no longer a small-sample fluke)
- **Brier score:** 0.117
- **Layer 2 recall (fraud caught):** 80% (12 of 15)
- **Layer 2 precision:** 43% — when the calibrator fires, roughly half the time it's a real fraud
- **Layer 2 specificity (non-fraud correctly rejected):** 88% (113 of 129)
- **Layer 1 fraud recall** (suspicion_score ≥ p90): **67%** (10 of 15 known frauds)
- **Layer 1 fraud recall** (suspicion_score ≥ p85): **93%** (14 of 15)
- **Layer 1 specificity on NORMAL tokens** (p90 cutoff): 58% — i.e., of 100
  tokens researched as NORMAL, 58 are correctly below p90 and 42 are above.
  The high-scoring NORMAL tokens are concentrated in high-volatility memecoins
  and blue-chip exchange/LST tokens whose on-chain behavior mimics fraud
  signatures even though research confirms them legitimate — exactly the
  failure mode Layer 2 is designed to catch.

## Honest misses (failures worth acknowledging)

- **HYPER (honeypot FRAUD, Etherscan-flagged)** — Layer 1 rated it suspicion 0.45
  and Layer 2 scored P(fraud) = 0.09. Small-volume contract that doesn't
  exhibit classic rug-pull features; we'd need graph-level signals (deployer
  reputation, liquidity-removal events) to catch it.
- **KUBO (impersonation FRAUD)** — similar miss; obfuscated function names
  are visible in bytecode but not in our trade-volume features.
- **TETH (BUG)** still scores P(fraud) = 0.88 — calibrator can't distinguish
  a precision-bug panic from a rug-pull panic on volume features alone.

## Headline calibration examples (from artifacts/validated_risk_scores.csv)

| Token | Real label | Votes | Suspicion | P(fraud) LOO | Verdict |
|---|---|:-:|:-:|:-:|---|
| WFT | FRAUD | 3 | 0.98 | **0.99** | Correct — top candidate |
| GREED | FRAUD | 1 | 0.96 | **0.89** | Correct |
| ORBDEG | FRAUD | 1 | 0.83 | **0.89** | Coordinated rug cluster caught |
| SPHERUM | FRAUD | 1 | 0.83 | **0.89** | Same cluster |
| ORBS | FRAUD | 1 | 0.83 | **0.89** | Same cluster |
| MAYNU | FRAUD | 1 | 0.86 | **0.88** | Correct |
| VAL | FRAUD | 1 | 0.95 | **0.86** | Correct |
| URL | FRAUD | 3 | 0.99 | **0.86** | Correct |
| YJM | FRAUD | 0 | 0.90 | **0.84** | Caught by continuous score despite 0 votes |
| PLASMA | FRAUD | 0 | 0.91 | **0.81** | Same |
| CZI | FRAUD | 0 | 0.88 | **0.52** | Correct, lower confidence |
| HYPER | FRAUD | 0 | 0.45 | 0.09 | **Missed** — too small to fit volume profile |
| KUBO | FRAUD | 1 | 0.99 | 0.12 | **Missed** — Layer 1 caught, Layer 2 didn't |
| TETH | BUG | 3 | 1.00 | 0.88 | False positive — Layer 2 can't tell bugs from rugs |
| WLFI | NORMAL | 3 | 1.00 | **0.005** | Correctly dismissed — 3-vote false alarm cleared |
| STRAT | NORMAL | 2 | 0.99 | **0.003** | Correctly low |
| DEGEN | NORMAL | 3 | 0.99 | **0.06** | Correctly normalized |
| 3Crv | BENIGN | 3 | 0.98 | **0.003** | Correctly low — institutional rebalancing |
| MIM | SHOCK | 3 | 0.98 | **0.002** | Correctly low — de-peg contagion |
| SLP | HACK | 1 | 0.95 | **0.003** | Correctly low — Ronin hack |
| wstUSR | HACK | 0 | 0.88 | **0.04** | Correctly low — Resolv Labs exploit |
| WILD | BUG | 0 | 0.84 | **0.01** | Correctly low — pLONGWILD cascade |

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
