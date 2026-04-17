# Unsupervised Anomaly Detection on ERC-20 Token Price & Volume Data

**Cecilia Cai | Harvard MDS Capstone | April 9, 2026**

---

## Objective

- **Goal**: Identify suspicious ERC-20 tokens from price & volume data — without any labels
- **Data**: 4,334 tokens, 4 features from Gillian's Price & Volume Dynamic Query
- **Approach**: 3 unsupervised anomaly detection methods, then vote to find consensus anomalies

---

## Features at a Glance

| Feature | What It Captures |
|---------|-----------------|
| `volume_spike_ratio` | How extreme the biggest volume day was vs. normal |
| `absolute_max_daily_volume_usd` | Peak single-day trading volume in USD |
| `total_days_traded` | Token lifespan (fewer days = possible rug pull) |
| `max_trade_dominance` | Max share of daily volume from one trader |

![Feature Distributions](feature_distributions.png)

---

## Feature Correlations

![Correlation Matrix](feature_correlation.png)

- Features are largely **uncorrelated** — each captures a different dimension of risk
- This means combining them gives us a richer anomaly signal

---

## Method 1: Isolation Forest

**Idea**: Anomalies are "easy to isolate" — they need fewer random splits to separate from the crowd.

- Contamination set at 5%
- **Result: 217 anomalies detected**

## Method 2: DBSCAN Clustering

**Idea**: Group tokens by behavioral similarity. Tokens that belong to **no group** (noise points) are anomalies.

![K-Distance Plot for eps Selection](dbscan_k_distance.png)

- eps = 1.5, min_samples = 10
- **Result: 46 noise points (most extreme anomalies)**

## Method 3: PCA + Mahalanobis Distance

**Idea**: Compress 4 features into 2 dimensions (PCA), then measure each token's distance from the center — accounting for the data's shape.

- PC1 + PC2 explain **68.6%** of total variance
- Threshold: top 5% by Mahalanobis distance
- **Result: 217 anomalies detected**

---

## PCA Visualization

![PCA Anomaly Scatter](pca_anomaly_scatter.png)

- **Left**: Colored by Mahalanobis distance (darker = further from center = more anomalous)
- **Right**: Red dots = Isolation Forest anomalies
- YODA, YANG, MIM, WLFI clearly isolated from the main cluster

---

## Consensus: 3-Method Voting

| Flagged by | Count |
|-----------|-------|
| 1 method only | less reliable |
| >= 2 methods | **153 tokens** |
| All 3 methods | **46 tokens** (highest confidence) |

We trust tokens flagged by **multiple methods** — reduces false positives.

---

