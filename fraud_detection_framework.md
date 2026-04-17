# Crypto Fraud Detection Framework: Multi-Dimensional Risk Scoring for Small-Cap ERC-20 Tokens

**Team**: Gillian Schriever, Cecilia Cai, Zhilin Chen, Jinghan Huang
**Program**: Master of Data Science, Harvard University
**Date**: March 2026

---

## 1. Executive Summary

This document proposes a multi-dimensional risk scoring framework for detecting market manipulation in small-cap ERC-20 tokens on Ethereum. Rather than treating fraud detection as a binary classification problem, we model it as a **multi-dimensional anomaly scoring system** that evaluates each token across several fraud dimensions simultaneously and outputs a risk profile.

The framework is designed to work **without labeled fraud data** — a critical constraint in crypto markets where ground truth is rarely available. Instead, it combines rule-based statistical thresholds with unsupervised anomaly detection, validated through known case studies.

---

## 2. Problem Statement

### 2.1 The Challenge

Small-cap ERC-20 tokens are highly vulnerable to manipulation due to low liquidity, limited regulatory oversight, and concentrated ownership. Common manipulation schemes include pump-and-dump, wash trading, rug pulls, and insider accumulation.

### 2.2 Why Traditional Classification Fails

A supervised classification approach (i.e., "train a model to predict fraud") faces fundamental obstacles in this domain:

1. **No ground truth**: There is no authoritative database of confirmed crypto fraud. SEC enforcement actions cover only a tiny fraction, and most manipulation goes unreported.
2. **Insufficient sample size**: Our candidate pool contains 50 tokens with only 4 having sufficient CEX transfer data. This is far too few to train a reliable classifier.
3. **Non-mutually-exclusive categories**: A single token can exhibit multiple fraud patterns simultaneously (e.g., wash trading to inflate volume *before* a pump-and-dump).
4. **Evolving tactics**: Manipulation strategies adapt over time; a model trained on historical patterns may miss novel schemes.

### 2.3 Our Approach

We reframe the problem from **"Is this token fraudulent?"** to **"How suspicious is this token across multiple manipulation dimensions?"**

```
Token → [Feature Extraction] → [Per-Dimension Risk Scoring] → Risk Profile
```

Output example:
```
Token X Risk Profile:
  Pump-and-Dump Risk:         0.82 (HIGH)
  Wash Trading Risk:          0.45 (MEDIUM)
  Rug Pull Risk:              0.15 (LOW)
  Insider Accumulation Risk:  0.71 (HIGH)
  Overall Manipulation Risk:  0.73 (HIGH)
```

---

## 3. Fraud Taxonomy

We define five fraud categories based on academic literature, industry reports, and input from our industry partners. Each category is paired with observable on-chain and off-chain behavioral indicators.

### 3.1 Pump-and-Dump (P&D)

**Definition**: Coordinated scheme where insiders accumulate tokens, artificially inflate the price through hype or fake demand, then sell at the peak — leaving other buyers with losses.

**Observable Indicators**:

| Indicator | Description | Data Source |
|-----------|-------------|-------------|
| Price spike ratio | Max daily return / average daily return | `prices.usd` |
| Volume spike ratio | Max daily volume / average daily volume | `prices.usd`, `dex.trades` |
| Pre-spike inflow surge | Exchange inflow count in N days before price peak | `erc20_ethereum.evt_Transfer` |
| Post-spike outflow surge | Exchange outflow count in N days after price peak | `erc20_ethereum.evt_Transfer` |
| Price reversal speed | Days from peak to 50% drawdown | `prices.usd` |
| Concentration before spike | Top-10 holder % in days leading up to spike | `erc20_ethereum.evt_Transfer` |

### 3.2 Wash Trading

**Definition**: An entity trades with itself (or colluding parties) to artificially inflate trading volume, creating the illusion of market activity.

**Observable Indicators**:

| Indicator | Description | Data Source |
|-----------|-------------|-------------|
| Round-trip wallets | Wallets appearing in both top sender and top receiver lists for exchange flows | `erc20_ethereum.evt_Transfer` |
| Volume-holder mismatch | High trading volume relative to number of unique holders | `dex.trades`, `evt_Transfer` |
| Transfer regularity | Unusually uniform time intervals between transfers (automated) | `erc20_ethereum.evt_Transfer` |
| Circular transfer chains | A → B → C → A patterns in wallet-to-wallet transfers | `erc20_ethereum.evt_Transfer` |
| Volume concentration | % of total volume contributed by top-5 trading wallets | `dex.trades` |

### 3.3 Rug Pull

**Definition**: Token creators or insiders suddenly withdraw all liquidity or dump their holdings, making the token worthless.

**Observable Indicators**:

| Indicator | Description | Data Source |
|-----------|-------------|-------------|
| Liquidity removal | Sudden drop in DEX liquidity pool balance | `dex.trades`, LP token transfers |
| Developer wallet outflow | Large transfers from deployer/known dev wallets | `erc20_ethereum.evt_Transfer` |
| Token age at collapse | Very young tokens (< 90 days) with sudden price collapse | `prices.usd` |
| Contract permissions | Mint/burn/pause functions callable by owner | Contract ABI analysis |
| Holder exodus | Rapid decline in unique holder count | `erc20_ethereum.evt_Transfer` |

### 3.4 Insider Accumulation

**Definition**: A small group of wallets quietly accumulates a dominant share of token supply before any price movement, giving them power to move the market.

**Observable Indicators**:

| Indicator | Description | Data Source |
|-----------|-------------|-------------|
| Wallet Gini coefficient | Inequality of token distribution across holders | `erc20_ethereum.evt_Transfer` |
| Top-N concentration | % of supply held by top 1/5/10/20 wallets | `erc20_ethereum.evt_Transfer` |
| Concentration trend | Rate of change in top-10 holder % over time | `erc20_ethereum.evt_Transfer` |
| Accumulation during low volume | Large transfers occurring when price/volume are dormant | `evt_Transfer`, `prices.usd` |
| Connected wallet clusters | Multiple top holders linked by direct transfers | `erc20_ethereum.evt_Transfer` |

### 3.5 Fake Volume / Market Manipulation

**Definition**: Broader category covering spoofing, layering, or other tactics to misrepresent market conditions.

**Observable Indicators**:

| Indicator | Description | Data Source |
|-----------|-------------|-------------|
| Price-volume decorrelation | Volume spikes without corresponding price movement | `prices.usd`, `dex.trades` |
| Exchange flow Gini | Concentration of exchange deposits/withdrawals among few wallets | `erc20_ethereum.evt_Transfer` |
| Cross-exchange inconsistency | Price or volume divergence across different exchanges | `dex.trades`, CEX data |
| Temporal clustering | Transfers clustered in narrow time windows (coordinated) | `erc20_ethereum.evt_Transfer` |

---

## 4. Feature Engineering

For each candidate token, we extract a standardized feature vector from on-chain and off-chain data.

### 4.1 Price & Volume Features

| Feature | Computation |
|---------|-------------|
| `price_spike_ratio` | max(daily_return) / mean(abs(daily_return)) |
| `max_drawdown` | Largest peak-to-trough decline |
| `volume_spike_ratio` | max(daily_volume) / median(daily_volume) |
| `price_volume_corr` | Pearson correlation between daily price change and volume |
| `volatility_clustering` | Autocorrelation of squared returns (GARCH-like) |
| `return_skewness` | Skewness of daily returns (positive = pump-like) |
| `return_kurtosis` | Kurtosis of daily returns (high = fat tails / extreme events) |

### 4.2 Exchange Flow Features

| Feature | Computation |
|---------|-------------|
| `net_flow` | Total inflow count - total outflow count |
| `inflow_ratio` | Inflow / (inflow + outflow) |
| `max_daily_inflow_zscore` | Z-score of the largest single-day inflow |
| `pre_spike_inflow` | Inflow count in 7 days before largest price spike |
| `post_spike_outflow` | Outflow count in 7 days after largest price spike |
| `flow_gini_inflow` | Gini coefficient of inflow sender distribution |
| `flow_gini_outflow` | Gini coefficient of outflow receiver distribution |
| `roundtrip_wallet_count` | Wallets in both top-10 senders and top-10 receivers |
| `exchange_count` | Number of distinct exchanges with activity |

### 4.3 Wallet Concentration Features

| Feature | Computation |
|---------|-------------|
| `wallet_gini` | Gini coefficient of all holder balances |
| `top1_pct` | % of supply held by top-1 wallet |
| `top5_pct` | % of supply held by top-5 wallets |
| `top10_pct` | % of supply held by top-10 wallets |
| `top20_pct` | % of supply held by top-20 wallets |
| `holder_count` | Total unique holders |
| `concentration_trend` | Slope of top-10 holder % over trailing 30 days |

### 4.4 Structural / Network Features

| Feature | Computation |
|---------|-------------|
| `unique_sender_count` | Distinct addresses that have sent this token |
| `unique_receiver_count` | Distinct addresses that have received this token |
| `transfer_regularity` | Std dev of inter-transfer time intervals (low = automated) |
| `large_transfer_pct` | % of transfers in top 1% by value |

---

## 5. Risk Scoring Methodology

### 5.1 Layer 1: Rule-Based Statistical Scoring

For each fraud dimension, we compute a risk score between 0 and 1 using statistical thresholds derived from the distribution of features across all candidate tokens.

**Scoring approach**: For each feature, compute its percentile rank within the candidate pool. Then combine relevant features into a per-dimension score using a weighted average.

```
Pump-and-Dump Score = weighted_avg(
    percentile(price_spike_ratio),        weight=0.25
    percentile(volume_spike_ratio),       weight=0.20
    percentile(pre_spike_inflow),         weight=0.20
    percentile(post_spike_outflow),       weight=0.15
    percentile(concentration_before),     weight=0.10
    percentile(price_reversal_speed),     weight=0.10
)
```

Weights are initially set by domain knowledge and can be tuned through case study validation.

**Advantages**:
- Does not require labeled data
- Transparent and interpretable
- Easy to adjust thresholds and weights

**Risk level thresholds**:
- 0.0 – 0.3: LOW
- 0.3 – 0.6: MEDIUM
- 0.6 – 0.8: HIGH
- 0.8 – 1.0: CRITICAL

### 5.2 Layer 2: Unsupervised Anomaly Detection

In parallel with rule-based scoring, we apply unsupervised methods on the full feature vector to detect tokens that are statistical outliers — potentially capturing fraud patterns not covered by our predefined rules.

**Methods**:

1. **Isolation Forest**: Identifies tokens that are easy to isolate in feature space (anomalous).
2. **DBSCAN Clustering**: Groups tokens by behavioral similarity; tokens that fall into no cluster (noise points) are flagged.
3. **PCA + Mahalanobis Distance**: Reduce dimensionality, then compute distance from the centroid — high distance = anomalous.

**Output**: An anomaly score (0–1) per token, independent of fraud category.

### 5.3 Layer 3: Composite Risk Profile

The final output combines both layers:

```
Overall Risk Score = α × Rule-Based Score + (1 - α) × Anomaly Score
```

Where α is a tunable parameter (default: 0.7, favoring the interpretable rule-based component).

---

## 6. Validation Strategy

Since we lack labeled data for traditional train/test evaluation, we use a **case study validation** approach.

### 6.1 Known Positive Cases (Expected High Risk)

Select 2–3 tokens with strong community consensus or documented evidence of manipulation:
- **BIRD**: Textbook pump-and-dump (Jul 2024 spike, pre-pump accumulation to 100% top-1 concentration, followed by price collapse)
- **LAND**: Wash trading evidence (round-trip wallets, inflow-dominated flow)

**Expectation**: These tokens should score HIGH or CRITICAL on the relevant fraud dimensions.

### 6.2 Known Negative Cases (Expected Low Risk)

Select 2–3 established, liquid ERC-20 tokens as a control group (e.g., USDC, UNI, LINK — if data is available).

**Expectation**: These tokens should score LOW across all fraud dimensions.

### 6.3 Sensitivity Analysis

- Vary scoring weights by ±20% and observe how token rankings change
- Test different anomaly detection methods and compare consistency
- Vary statistical thresholds (e.g., z-score cutoff from 2.0 to 3.0) and measure impact

### 6.4 Partner Review

Present risk profiles to industry partners (Lumberg, MiLLi3e, uberjake) and solicit expert feedback on whether the flagged tokens and risk levels align with their domain experience.

---

## 7. New Token Assessment Pipeline

For any new ERC-20 token, the assessment follows this pipeline:

```
┌─────────────────────────────────────────────────────┐
│  INPUT: Token contract address                       │
├─────────────────────────────────────────────────────┤
│  Step 1: Data Collection                             │
│    - Query prices.usd for price/volume history       │
│    - Query evt_Transfer for wallet balances & flows  │
│    - Query cex_ethereum.addresses for exchange flows │
│    - Query dex.trades for DEX activity               │
├─────────────────────────────────────────────────────┤
│  Step 2: Feature Extraction                          │
│    - Compute all features from Section 4             │
│    - Normalize against candidate pool distribution   │
├─────────────────────────────────────────────────────┤
│  Step 3: Risk Scoring                                │
│    - Layer 1: Rule-based scores per fraud dimension  │
│    - Layer 2: Unsupervised anomaly score             │
│    - Layer 3: Composite risk profile                 │
├─────────────────────────────────────────────────────┤
│  OUTPUT: Risk Profile                                │
│    Pump-and-Dump Risk:         0.82 (HIGH)           │
│    Wash Trading Risk:          0.45 (MEDIUM)         │
│    Rug Pull Risk:              0.15 (LOW)            │
│    Insider Accumulation Risk:  0.71 (HIGH)           │
│    Anomaly Score:              0.68 (HIGH)           │
│    Overall Manipulation Risk:  0.73 (HIGH)           │
│    Most Likely Type:           Pump-and-Dump         │
└─────────────────────────────────────────────────────┘
```

---

## 8. Early Warning Extension (If Time Permits)

Beyond static risk scoring, we can build a temporal early warning system:

### 8.1 Approach

Instead of asking "is this token fraudulent?", ask: **"Is this token's risk score increasing?"**

Monitor time-series features (e.g., rolling 7-day concentration trend, inflow acceleration) and trigger alerts when:
- Any single-dimension risk score crosses from MEDIUM to HIGH
- Multiple dimensions increase simultaneously
- Feature trajectories match historical pre-fraud patterns from our case studies

### 8.2 Implementation

- Compute risk scores on a rolling window (e.g., recalculate daily)
- Define alert rules: "If pump-and-dump score increases by >0.2 in 7 days, flag for review"
- Output: time-series of risk scores with alert annotations

---

## 9. Project Timeline

| Week | Phase | Deliverable |
|------|-------|-------------|
| 1–2 | Scope & Alignment | Finalized fraud taxonomy, confirmed with partners |
| 3–4 | Data Pipeline & EDA | Reproducible data pipelines, initial EDA (price/volume + exchange flow + wallet concentration) |
| 5–6 | Feature Engineering | Complete feature extraction for all candidate tokens |
| 7–8 | Risk Scoring (Layer 1) | Rule-based scoring system, per-dimension risk scores |
| 9–10 | Risk Scoring (Layer 2) + Validation | Unsupervised anomaly detection, case study validation, composite scoring |
| 11–12 | MVP Dashboard | Interactive risk profile output, alert visualization |
| 13–14 | Final Package | Presentation, technical report, reproducible codebase, documented limitations |

---

## 10. Known Limitations & Mitigations

| Limitation | Impact | Mitigation |
|-----------|--------|------------|
| No labeled ground truth | Cannot compute precision/recall | Case study validation + expert review |
| Small sample size (50 tokens, 4 with CEX data) | Statistical thresholds may be unstable | Expand to DEX data; use percentile-based scoring |
| CEX address coverage gaps | May miss exchange flows on unlisted exchanges | Supplement with Dune community labels; include DEX flows |
| Token decimal normalization | Raw `value` field not directly comparable across tokens | Fetch decimal metadata per contract and normalize |
| DEX flows not yet included | 46 of 50 tokens have no CEX data | Add `dex.trades` analysis in Phase 3 |
| Adversarial adaptation | Fraudsters may change tactics | Design modular framework so new indicators can be added |
| Single-chain focus | Only Ethereum L1 | Document as limitation; framework is extensible to L2/other chains |

---

## 11. Ethical Considerations

1. **All data is public**: Ethereum blockchain is public by design. No PII is collected or processed.
2. **Probabilistic, not definitive**: We output risk scores, not fraud verdicts. No token is labeled as "fraudulent" — only "statistically anomalous" or "high risk."
3. **Dual-use risk**: Detection methods could theoretically be reverse-engineered to improve evasion. We mitigate this by keeping specific thresholds and weights configurable rather than hardcoded.
4. **Research scope**: This is an academic research project, not a legal or regulatory tool. Findings are not intended as evidence of wrongdoing.

---

## Appendix A: Data Sources

| Source | Table / API | Description |
|--------|-------------|-------------|
| Dune Analytics | `erc20_ethereum.evt_Transfer` | All ERC-20 token transfers on Ethereum |
| Dune Analytics | `cex_ethereum.addresses` | Known CEX wallet addresses (4,366 addresses, 318 exchanges) |
| Dune Analytics | `prices.usd` | Token prices aggregated per minute |
| Dune Analytics | `dex.trades` | Decentralized exchange trade records |
| CoinGecko API | `/coins/{id}/market_chart` | Historical OHLCV and market cap data |
| Candidate Tokens | `candidate_tokens.json` | 50 pre-screened volatile small-cap tokens |

## Appendix B: Team Module Mapping

| Team Member | Module | Key Features Contributed |
|-------------|--------|------------------------|
| Teammate (Wallet Concentration) | Wallet / Ownership Concentration | `wallet_gini`, `top_N_pct`, `holder_count`, `concentration_trend` |
| Cecilia Cai (Exchange Inflow/Outflow) | Exchange Flow Analysis | `net_flow`, `inflow_ratio`, `flow_gini`, `roundtrip_wallet_count`, `pre_spike_inflow` |
| [TBD] | Price & Volume Dynamics | `price_spike_ratio`, `volume_spike_ratio`, `return_skewness` |
| [TBD] | Network / Structural Analysis | `transfer_regularity`, `circular_chains`, `connected_clusters` |
