"""
Model evaluation: sensitivity + baseline.

Two slides' worth of evidence in one script.

 1. Sensitivity: how stable is the 3-vote consensus set as we sweep the
    contamination / percentile threshold? Kills the "5% threshold was
    cherry-picked" objection.

 2. Baseline: does the 3-model ensemble actually beat a naive single-feature
    threshold at recovering known-fraud tokens? Answers "what's the lift
    from all this machinery?"
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.spatial.distance import mahalanobis
from sklearn.cluster import DBSCAN
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts"

FEATURES = [
    "volume_spike_ratio",
    "absolute_max_daily_volume_usd",
    "total_days_traded",
    "max_trade_dominance",
    "early_velocity_ratio",
    "early_trade_dominance",
]
LOG_FEATURES = {"volume_spike_ratio", "absolute_max_daily_volume_usd"}


def build_features(df: pd.DataFrame) -> np.ndarray:
    X = df[FEATURES].copy()
    for col in LOG_FEATURES:
        X[col] = np.log1p(X[col].clip(lower=0))
    return StandardScaler().fit_transform(X.values)


def run_ensemble(X: np.ndarray, contamination: float, pct: float) -> np.ndarray:
    iso = IsolationForest(contamination=contamination, random_state=42).fit(X)
    iso_flag = iso.predict(X) == -1

    dbscan_flag = DBSCAN(eps=1.5, min_samples=10).fit_predict(X) == -1

    pca = PCA(n_components=3, random_state=42).fit_transform(X)
    cov = np.cov(pca, rowvar=False)
    inv_cov = np.linalg.inv(cov)
    center = pca.mean(axis=0)
    dists = np.array([mahalanobis(r, center, inv_cov) for r in pca])
    pca_flag = dists > np.percentile(dists, pct)

    return iso_flag.astype(int) + dbscan_flag.astype(int) + pca_flag.astype(int)


def sensitivity_sweep(df: pd.DataFrame, X: np.ndarray) -> pd.DataFrame:
    rows = []
    for c in [0.03, 0.05, 0.07, 0.10]:
        pct = 100 * (1 - c)
        votes = run_ensemble(X, c, pct)
        validated = df["is_validated"] == 1
        fraud_mask = df["is_fraud"] == 1
        for k in [1, 2, 3]:
            at_least_k = votes >= k
            n_flagged = int(at_least_k.sum())
            n_val = int((at_least_k & validated).sum())
            n_fraud_caught = int((at_least_k & fraud_mask).sum())
            rows.append({
                "contamination": c,
                "vote_threshold": f"≥{k}",
                "n_flagged": n_flagged,
                "n_validated_flagged": n_val,
                "n_fraud_caught": n_fraud_caught,
                "fraud_recall": round(n_fraud_caught / max(int(fraud_mask.sum()), 1), 3),
                "flag_rate_pct": round(100 * n_flagged / len(df), 2),
            })
    return pd.DataFrame(rows)


def baseline_comparison(df: pd.DataFrame, X: np.ndarray) -> pd.DataFrame:
    votes = run_ensemble(X, contamination=0.05, pct=95)
    n = len(df)
    total_fraud = int((df["is_fraud"] == 1).sum())

    rows = []

    # Strategy A: naive single-feature threshold on volume_spike_ratio.
    thresh = np.percentile(df["volume_spike_ratio"], 95)
    naive_flag = df["volume_spike_ratio"] > thresh
    rows.append({
        "strategy": f"Naive: volume_spike_ratio > p95 ({thresh:.1f}x)",
        "n_flagged": int(naive_flag.sum()),
        "flag_rate_pct": round(100 * naive_flag.sum() / n, 2),
        "fraud_caught": int((naive_flag & (df["is_fraud"] == 1)).sum()),
        "fraud_recall": round(int((naive_flag & (df["is_fraud"] == 1)).sum()) / max(total_fraud, 1), 3),
    })

    # Strategy B: random 5% sample — what you'd get from no model at all.
    rng = np.random.default_rng(42)
    n_draws = 100
    recalls = []
    for _ in range(n_draws):
        sample_idx = rng.choice(n, size=int(0.05 * n), replace=False)
        mask = np.zeros(n, dtype=bool)
        mask[sample_idx] = True
        recalls.append((mask & (df["is_fraud"].values == 1)).sum() / max(total_fraud, 1))
    rows.append({
        "strategy": "Random 5% sample (expected)",
        "n_flagged": int(0.05 * n),
        "flag_rate_pct": 5.0,
        "fraud_caught": round(float(np.mean(recalls)) * total_fraud, 1),
        "fraud_recall": round(float(np.mean(recalls)), 3),
    })

    # Strategy C: our ensemble, ≥2 votes.
    ens_flag = votes >= 2
    rows.append({
        "strategy": "Ensemble (≥2 votes)",
        "n_flagged": int(ens_flag.sum()),
        "flag_rate_pct": round(100 * ens_flag.sum() / n, 2),
        "fraud_caught": int((ens_flag & (df["is_fraud"].values == 1)).sum()),
        "fraud_recall": round(int((ens_flag & (df["is_fraud"].values == 1)).sum()) / max(total_fraud, 1), 3),
    })

    # Strategy D: ensemble, all 3 votes.
    ens3 = votes == 3
    rows.append({
        "strategy": "Ensemble (3 votes)",
        "n_flagged": int(ens3.sum()),
        "flag_rate_pct": round(100 * ens3.sum() / n, 2),
        "fraud_caught": int((ens3 & (df["is_fraud"].values == 1)).sum()),
        "fraud_recall": round(int((ens3 & (df["is_fraud"].values == 1)).sum()) / max(total_fraud, 1), 3),
    })

    # Strategy E: continuous suspicion_score threshold. This is the punchline —
    # discrete voting drops frauds that any single model misses, but the
    # rank-averaged continuous score catches them.
    for pct in [90, 85]:
        thresh = np.percentile(df["suspicion_score"], pct)
        flag = df["suspicion_score"] >= thresh
        rows.append({
            "strategy": f"Ensemble (suspicion_score ≥ p{pct} = {thresh:.3f})",
            "n_flagged": int(flag.sum()),
            "flag_rate_pct": round(100 * flag.sum() / n, 2),
            "fraud_caught": int((flag & (df["is_fraud"] == 1)).sum()),
            "fraud_recall": round(int((flag & (df["is_fraud"] == 1)).sum()) / max(total_fraud, 1), 3),
        })

    return pd.DataFrame(rows)


def plot_sensitivity(sens: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))

    pivot = sens.pivot(index="contamination", columns="vote_threshold", values="n_flagged")
    pivot.plot(kind="bar", ax=axes[0], color=["#bdc3c7", "#7f8c8d", "#2c3e50"])
    axes[0].set_title("Flagged-token count by contamination × vote threshold")
    axes[0].set_ylabel("Tokens flagged")
    axes[0].set_xlabel("Contamination parameter")
    axes[0].legend(title="Votes", loc="upper right")
    axes[0].tick_params(axis="x", rotation=0)

    three = sens[sens["vote_threshold"] == "≥3"]
    axes[1].plot(three["contamination"], three["fraud_recall"], "o-", color="#c0392b", linewidth=2)
    axes[1].set_title("Fraud recall (3-vote consensus) across contamination sweep")
    axes[1].set_xlabel("Contamination parameter")
    axes[1].set_ylabel("Fraud recall (validated set)")
    axes[1].set_ylim(0, 1.05)
    axes[1].grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(ARTIFACTS / "sensitivity_sweep.png", dpi=300)
    plt.close(fig)


def plot_baseline(baseline: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(11, 5.5))
    palette = {
        "Naive": "#bdc3c7",
        "Random": "#bdc3c7",
        "Ensemble (≥2": "#3498db",
        "Ensemble (3": "#3498db",
        "Ensemble (suspicion": "#27ae60",
    }
    colors = [
        next((v for k, v in palette.items() if s.startswith(k)), "#95a5a6")
        for s in baseline["strategy"]
    ]
    ax.barh(baseline["strategy"], baseline["fraud_recall"], color=colors)
    for i, (recall, n_flag) in enumerate(zip(baseline["fraud_recall"], baseline["n_flagged"])):
        ax.text(recall + 0.01, i, f"{recall:.0%}  (flagged {n_flag})", va="center", fontsize=9)
    ax.set_xlim(0, 1.15)
    ax.set_xlabel("Fraud recall across the n=6 validated-fraud subset")
    ax.set_title("Continuous suspicion score > discrete voting: lift over baselines")
    ax.invert_yaxis()
    fig.tight_layout()
    fig.savefig(ARTIFACTS / "baseline_comparison.png", dpi=300)
    plt.close(fig)


def main() -> None:
    df = pd.read_csv(ARTIFACTS / "tokens_scored.csv")
    X = build_features(df)

    sens = sensitivity_sweep(df, X)
    sens.to_csv(ARTIFACTS / "sensitivity_sweep.csv", index=False)
    plot_sensitivity(sens)

    baseline = baseline_comparison(df, X)
    baseline.to_csv(ARTIFACTS / "baseline_comparison.csv", index=False)
    plot_baseline(baseline)

    print("=" * 60)
    print("Sensitivity sweep (contamination × vote threshold):")
    print("=" * 60)
    print(sens.to_string(index=False))
    print()
    print("=" * 60)
    print("Baseline comparison:")
    print("=" * 60)
    print(baseline.to_string(index=False))


if __name__ == "__main__":
    main()
