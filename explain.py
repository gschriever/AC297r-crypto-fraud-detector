"""
SHAP-based explainability for Layer 1.

We explain the Isolation Forest's anomaly decision (not DBSCAN, which has
no per-sample attribution, and not PCA/Mahalanobis, which is a distance
metric not a learned model). One force-like plot per headline token answers:
"which features pushed this token into the suspicious bucket?"
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
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

HEADLINE_TOKENS = ["TETH", "SLP", "3Crv", "PLASMA", "CZI", "GREED", "MIM", "VAL", "YANG", "WFT"]


def build_model(df: pd.DataFrame) -> tuple[IsolationForest, np.ndarray, pd.DataFrame]:
    X_raw = df[FEATURES].copy()
    for col in LOG_FEATURES:
        X_raw[col] = np.log1p(X_raw[col].clip(lower=0))
    X_scaled = StandardScaler().fit_transform(X_raw.values)

    iso = IsolationForest(contamination=0.05, random_state=42)
    iso.fit(X_scaled)
    return iso, X_scaled, X_raw


def compute_shap_values(iso: IsolationForest, X_scaled: np.ndarray) -> np.ndarray:
    # TreeExplainer works directly on IsolationForest — no surrogate needed.
    # Output: SHAP values for the anomaly score (lower = more anomalous).
    explainer = shap.TreeExplainer(iso)
    return explainer.shap_values(X_scaled)


def plot_per_token_contributions(
    df: pd.DataFrame, shap_values: np.ndarray, tokens: list[str]
) -> None:
    rows = [
        (sym, df.index[df["token_symbol"].str.lower() == sym.lower()].tolist())
        for sym in tokens
    ]
    rows = [(s, ix[0]) for s, ix in rows if ix]
    if not rows:
        print("No headline tokens found in dataset.")
        return

    n = len(rows)
    fig, axes = plt.subplots(n, 1, figsize=(10, 2.2 * n), sharex=True)
    if n == 1:
        axes = [axes]

    for ax, (symbol, idx) in zip(axes, rows):
        contribs = shap_values[idx]
        colors = ["#2980b9" if v >= 0 else "#c0392b" for v in contribs]
        ax.barh(FEATURES, contribs, color=colors)
        ax.axvline(0, color="black", linewidth=0.8)
        ax.set_title(
            f"{symbol}  (anomaly score = {df.loc[idx, 'iso_score']:.3f}, "
            f"votes = {int(df.loc[idx, 'consensus_votes'])}, "
            f"taxonomy = {df.loc[idx, 'taxonomy'] if pd.notna(df.loc[idx, 'taxonomy']) else '—'})",
            fontsize=10,
            loc="left",
        )

    axes[-1].set_xlabel("SHAP contribution to anomaly score  (red → pushes toward anomalous)")
    fig.suptitle("Per-token feature attribution (Isolation Forest)", fontsize=13)
    fig.tight_layout()
    fig.savefig(ARTIFACTS / "shap_headline_tokens.png", dpi=300)
    plt.close(fig)


def plot_global_importance(shap_values: np.ndarray) -> None:
    importance = np.abs(shap_values).mean(axis=0)
    order = np.argsort(importance)[::-1]
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.barh([FEATURES[i] for i in order][::-1], importance[order][::-1], color="#34495e")
    ax.set_xlabel("Mean |SHAP value|")
    ax.set_title("Global feature importance — Isolation Forest")
    fig.tight_layout()
    fig.savefig(ARTIFACTS / "shap_global_importance.png", dpi=300)
    plt.close(fig)


def main() -> None:
    df = pd.read_csv(ARTIFACTS / "tokens_scored.csv").reset_index(drop=True)
    iso, X_scaled, _ = build_model(df)
    shap_values = compute_shap_values(iso, X_scaled)

    plot_global_importance(shap_values)
    plot_per_token_contributions(df, shap_values, HEADLINE_TOKENS)

    global_imp = pd.DataFrame(
        {"feature": FEATURES, "mean_abs_shap": np.abs(shap_values).mean(axis=0).round(4)}
    ).sort_values("mean_abs_shap", ascending=False)
    global_imp.to_csv(ARTIFACTS / "shap_global_importance.csv", index=False)

    print("=" * 60)
    print("SHAP explainability complete.")
    print("=" * 60)
    print("Global importance (mean |SHAP|):")
    print(global_imp.to_string(index=False))
    print()
    print("Artifacts:")
    print("  artifacts/shap_global_importance.png")
    print("  artifacts/shap_headline_tokens.png")
    print("  artifacts/shap_global_importance.csv")


if __name__ == "__main__":
    main()
