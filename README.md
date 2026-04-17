# AC297r: Unsupervised Crypto Fraud Detector

An unsupervised machine learning pipeline designed to detect catastrophic market events and fraud in cryptocurrency trading data using consensus-based anomaly detection.

## 🚀 Overview
Traditional fraud detection relies on labeled datasets, which are rare and quickly outdated in the crypto space. This project implements a purely unsupervised approach—using **Isolation Forest**, **DBSCAN**, and **PCA** with Mahalanobis Distance—to isolate severe outliers without any prior knowledge of past scams.

## 🧠 Methodology: Severity via Consensus
The pipeline uses a "Consensus Voting" mechanism to rank anomalies:
- **3-Vote Anomalies**: Extremely high-confidence outliers flagged by all three models.
- **2-Vote Anomalies**: Significant market events.
- **1-Vote Anomalies**: Lower-confidence "noise" or generic market volatility.

## 🧪 Validation & Nuance (Results)
We validated over **80 tokens** from the detected outliers against real-world security reports, blockchain explorer data, and regulatory blacklists.

### 📐 Anomaly Detection Rate: 100%
Every single token flagged by the **3-Vote Consensus** was confirmed to be a legitimate "Black Swan" event (a mathematical extreme).

### ⚖️ Fraud vs. Anomaly Distinction
While the pipeline is 100% effective at finding *anomalies*, we must distinguish between "Malicious Fraud" and "Benign Market Shocks":
- **Fraud Detection Rate (~80%)**: Intentional developer fraud, including Rug Pulls, Honeypots, and brand-spoofing phishing drainers (e.g., **plasma**, **CZI**).
- **Benign Anomalies (~20%)**: Non-malicious events that exhibit identical volume signatures to fraud. This includes **Institutional rebalancing** (e.g., **3Crv**), **Internal protocol bugs** (e.g., **TETH**), or **External exploits/hacks** (e.g., **SLP**).

## 🛠 Project Structure
- `analyze_csv.py`: Core logic for feature extraction and outlier analysis.
- `evaluate_model.py`: Consensus voting implementation and scoring.
- `scrape_anomalies.py`: Automated validation scraping against web sources.
- `price_volume_features.sql`: Feature engineering queries.

## 📈 Visuals
The project includes automated visualization tools for mapping the anomaly space:
- `anomaly_scatter_plot.png`: Multi-dimensional outlier mapping.
- `fraud_validation_chart.png`: Classification of true vs. false positives.

---
*Created for the AC297r Capstone Project.*
