"""
AC297r Crypto Fraud Detector — canonical pipeline.

One command (`python pipeline.py`) produces every number and figure cited in
the final deck, under ./artifacts/. Two-layer model:

  Layer 1 (unsupervised): suspicious-behavior detection via an ensemble of
          Isolation Forest, DBSCAN, and PCA+Mahalanobis.
  Layer 2 (calibration):  P(fraud | suspicious) fit on the hand-labeled
          validation registry — computed in calibrate.py, which consumes
          artifacts/tokens_scored.csv.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import seaborn as sns
from scipy.spatial.distance import mahalanobis
from sklearn.cluster import DBSCAN
from sklearn.decomposition import PCA
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

# ---- Config ------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent
BASE_CSV = ROOT / "Gillian_Price_and_Volume_Dynamic_Query_with_Token_Boundary_Conditions_QUERY_EXPORT.csv"
TEMPORAL_CSV = ROOT / "dune queries" / "Temporal_Price_Volume_Dynamics_24h_Window_Extraction.csv"
# Optional BTC-normalized features produced by the v2 SQL
# (dune queries/price_volume_features_btc_normalized.sql).  When this file
# is present, the pipeline joins these columns in and the detectors can
# run on either the v1 (unadjusted) or v2 (BTC-adjusted) feature set.
BTC_NORMALIZED_CSV = ROOT / "dune queries" / "BTC_Normalized_Features_EXPORT.csv"
ARTIFACTS = ROOT / "artifacts"

RANDOM_STATE = 42
CONTAMINATION = 0.05
DBSCAN_EPS = 1.5
DBSCAN_MIN_SAMPLES = 10
MAHALANOBIS_PERCENTILE = 95

STATIC_FEATURES = [
    "volume_spike_ratio",
    "absolute_max_daily_volume_usd",
    "total_days_traded",
    "max_trade_dominance",
]
TEMPORAL_FEATURES = ["early_velocity_ratio", "early_trade_dominance"]
# BTC-normalized features — only used when BTC_NORMALIZED_CSV is present.
BTC_FEATURES = [
    "volume_spike_ratio_btc_adj",
    "pct_volume_on_btc_extreme_days",
    "peak_coincident_btc_extreme",
    "volume_correlation_btc",
]
LOG_FEATURES = {
    "volume_spike_ratio",
    "absolute_max_daily_volume_usd",
    "volume_spike_ratio_btc_adj",
}

# Validation registry — combines the original 14 hand-curated labels with
# an additional 55 web-researched labels (see validation_registry.csv).
# Schema: token_address, token_symbol, taxonomy, is_fraud, is_anomaly_expected,
#         confidence, source, justification, primary_source_url.
# Address-keyed (symbols collide on Ethereum). UNKNOWN rows are held out of
# supervised evaluation; NORMAL rows are true negatives for Layer 1.
VALIDATION_CSV = ROOT / "validation_registry.csv"


# ---- Load + merge ------------------------------------------------------------


def load_data() -> pd.DataFrame:
    base = pd.read_csv(BASE_CSV)
    temporal = pd.read_csv(TEMPORAL_CSV)

    df = base.merge(temporal, on="token_address", how="left")
    df["has_temporal_data"] = df["early_velocity_ratio"].notna()

    # Optional BTC-normalized features. The round 2 experiment showed that
    # including these directly in the Layer-1 ensemble *hurts* fraud recall
    # because short-lived rug pulls have degenerate BTC features (NaN /
    # zero correlation / zero overlap with BTC-extreme days) and get
    # pulled toward the "normal" center once the features are imputed.
    #
    # We therefore load them as diagnostic *annotations* only -- surfaced
    # in tokens_scored.csv as a per-token btc_contamination_score -- and
    # do not include them in the feature matrix that drives Isolation
    # Forest / DBSCAN / PCA.  Proper use: for any token the pipeline
    # flags as suspicious, consult btc_contamination_score to decide
    # whether the anomaly is likely BTC-driven noise.
    df["has_btc_normalized"] = False
    if BTC_NORMALIZED_CSV.exists():
        btc = pd.read_csv(BTC_NORMALIZED_CSV)
        keep = ["token_address"] + [c for c in BTC_FEATURES if c in btc.columns]
        df = df.merge(btc[keep], on="token_address", how="left")
        if BTC_FEATURES[0] in df.columns:
            df["has_btc_normalized"] = df[BTC_FEATURES[0]].notna()

    numeric_cols = STATIC_FEATURES + TEMPORAL_FEATURES
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
    df = df.dropna(subset=STATIC_FEATURES).copy()

    for col in TEMPORAL_FEATURES:
        df[col] = df[col].fillna(df[col].median())

    return df


def compute_btc_contamination(df: pd.DataFrame) -> pd.DataFrame:
    """Combine the four BTC-adjusted features into a 0-1 score describing
    how much of a token's volume signal is plausibly BTC-driven.

    Only meaningful for tokens with enough trading history to compute a
    reliable correlation -- typically >= 14 days.  For shorter-lived
    tokens the score is NaN (the BTC signal isn't defined on 1-day rugs).
    """
    if not all(c in df.columns for c in BTC_FEATURES):
        df["btc_contamination_score"] = np.nan
        return df

    eligible = df["total_days_traded"] >= 14
    corr = df["volume_correlation_btc"].clip(lower=-1, upper=1).fillna(0)
    pct_extreme = df["pct_volume_on_btc_extreme_days"].fillna(0).clip(lower=0, upper=1)
    peak = df["peak_coincident_btc_extreme"].fillna(0)

    # Weighted average of the three most-interpretable signals.  Correlation
    # gets the dominant weight because it's a robust continuous signal; the
    # two extreme-day indicators add texture.
    raw = 0.6 * corr.abs() + 0.3 * pct_extreme + 0.1 * peak
    df["btc_contamination_score"] = np.where(eligible, raw.clip(0, 1), np.nan)
    return df


# ---- Feature matrix ----------------------------------------------------------


def build_feature_matrix(df: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
    # Layer 1 uses v1 features only. BTC-adjusted features are reserved
    # for downstream annotation (see compute_btc_contamination).
    feature_cols = STATIC_FEATURES + TEMPORAL_FEATURES
    X = df[feature_cols].copy()
    for col in LOG_FEATURES:
        if col in X.columns:
            X[col] = np.log1p(X[col].clip(lower=0))
    X_scaled = StandardScaler().fit_transform(X.values)
    return X_scaled, feature_cols


# ---- Layer 1: three anomaly detectors ----------------------------------------


def run_detectors(df: pd.DataFrame, X: np.ndarray) -> tuple[pd.DataFrame, np.ndarray, PCA]:
    iso = IsolationForest(contamination=CONTAMINATION, random_state=RANDOM_STATE)
    iso.fit(X)
    df["iso_score"] = iso.decision_function(X)
    df["iso_flag"] = iso.predict(X) == -1

    dbscan = DBSCAN(eps=DBSCAN_EPS, min_samples=DBSCAN_MIN_SAMPLES)
    df["dbscan_flag"] = dbscan.fit_predict(X) == -1

    pca = PCA(n_components=3, random_state=RANDOM_STATE)
    X_pca = pca.fit_transform(X)
    cov = np.cov(X_pca, rowvar=False)
    inv_cov = np.linalg.inv(cov)
    center = X_pca.mean(axis=0)
    df["mahalanobis_dist"] = [mahalanobis(row, center, inv_cov) for row in X_pca]
    df["pca_flag"] = df["mahalanobis_dist"] > np.percentile(df["mahalanobis_dist"], MAHALANOBIS_PERCENTILE)

    df["consensus_votes"] = (
        df["iso_flag"].astype(int)
        + df["dbscan_flag"].astype(int)
        + df["pca_flag"].astype(int)
    )

    df["PCA1"], df["PCA2"], df["PCA3"] = X_pca[:, 0], X_pca[:, 1], X_pca[:, 2]
    return df, X_pca, pca


# ---- Layer 1 composite: continuous suspicion score ---------------------------


def score_suspicion(df: pd.DataFrame) -> pd.DataFrame:
    # Rank-percentile each continuous anomaly signal independently, then
    # average. Lower iso_score = more anomalous, so invert before ranking.
    iso_rank = (-df["iso_score"]).rank(pct=True)
    maha_rank = df["mahalanobis_dist"].rank(pct=True)
    df["suspicion_score"] = (iso_rank + maha_rank) / 2.0
    return df


# ---- Validation join ---------------------------------------------------------


def attach_validation(df: pd.DataFrame) -> pd.DataFrame:
    # Registry is address-keyed (symbols collide on Ethereum). Merge on
    # token_address, pulling in taxonomy + derived flags.
    reg = pd.read_csv(VALIDATION_CSV)
    reg = reg[["token_address", "taxonomy", "is_fraud", "is_anomaly_expected", "confidence"]]
    df = df.merge(reg, on="token_address", how="left")
    df["is_validated"] = df["taxonomy"].notna().astype(int)
    df["is_fraud"] = df["is_fraud"].fillna(0).astype(int)
    return df


# ---- Visualizations ----------------------------------------------------------

HEADLINE = {
    "TETH": "Protocol Bug",
    "SLP": "Ronin Hack",
    "3Crv": "Institutional Rebalancing",
    "plasma": "Phishing Drainer",
    "CZI": "Binance Impersonator",
    "GREED": "Exit Scam",
    "MIM": "UST Contagion",
}


def plot_static_map(df: pd.DataFrame) -> None:
    sns.set_style("whitegrid")
    fig, ax = plt.subplots(figsize=(14, 10))
    sns.scatterplot(
        data=df,
        x="PCA1",
        y="PCA2",
        hue="consensus_votes",
        size="suspicion_score",
        palette="viridis",
        sizes=(20, 200),
        alpha=0.6,
        edgecolor="none",
        ax=ax,
    )
    for _, row in df[df["token_symbol"].isin(HEADLINE)].iterrows():
        ax.annotate(
            f"{row['token_symbol']}\n({HEADLINE[row['token_symbol']]})",
            (row["PCA1"], row["PCA2"]),
            textcoords="offset points",
            xytext=(10, 10),
            fontsize=9,
            fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.7),
        )
    ax.set_title("Consensus Anomaly Map (PC1–PC2)", fontsize=16)
    ax.set_xlabel("PC1 (volume dynamics)")
    ax.set_ylabel("PC2 (temporal velocity)")
    ax.legend(title="Consensus votes", bbox_to_anchor=(1.05, 1), loc="upper left")
    fig.tight_layout()
    fig.savefig(ARTIFACTS / "anomaly_map_static.png", dpi=300)
    plt.close(fig)


def plot_interactive_map(df: pd.DataFrame) -> None:
    fig = px.scatter_3d(
        df,
        x="PCA1",
        y="PCA2",
        z="PCA3",
        color="consensus_votes",
        size="suspicion_score",
        hover_name="token_symbol",
        hover_data=["early_velocity_ratio", "max_trade_dominance", "total_days_traded", "taxonomy"],
        color_continuous_scale="Viridis",
        title="Consensus Anomaly Map — 3D PCA (hover to explore)",
    )
    fig.write_html(ARTIFACTS / "anomaly_map_interactive.html")


# ---- Manifest + entry point -------------------------------------------------


def write_artifacts(df: pd.DataFrame, pca: PCA) -> dict:
    ARTIFACTS.mkdir(exist_ok=True)

    scored_cols = [
        "token_address",
        "token_symbol",
        *STATIC_FEATURES,
        *TEMPORAL_FEATURES,
        "has_temporal_data",
        "iso_score",
        "iso_flag",
        "dbscan_flag",
        "mahalanobis_dist",
        "pca_flag",
        "consensus_votes",
        "suspicion_score",
        "btc_contamination_score",
        "PCA1",
        "PCA2",
        "PCA3",
        "taxonomy",
        "confidence",
        "is_fraud",
        "is_anomaly_expected",
        "is_validated",
    ]
    df[scored_cols].to_csv(ARTIFACTS / "tokens_scored.csv", index=False)

    three_vote = df[df["consensus_votes"] == 3].sort_values("suspicion_score", ascending=False)
    three_vote[scored_cols].to_csv(ARTIFACTS / "anomalies_3vote.csv", index=False)

    validated = df[df["is_validated"] == 1].sort_values("suspicion_score", ascending=False)
    validated[scored_cols].to_csv(ARTIFACTS / "validation_joined.csv", index=False)

    plot_static_map(df)
    plot_interactive_map(df)

    return {
        "n_tokens": int(len(df)),
        "n_with_temporal": int(df["has_temporal_data"].sum()),
        "n_1_vote": int((df["consensus_votes"] == 1).sum()),
        "n_2_vote": int((df["consensus_votes"] == 2).sum()),
        "n_3_vote": int((df["consensus_votes"] == 3).sum()),
        "n_validated_in_data": int(df["is_validated"].sum()),
        "pca_explained_variance_3": [round(v, 4) for v in pca.explained_variance_ratio_],
    }


def main() -> None:
    df = load_data()
    X, _ = build_feature_matrix(df)
    df, _, pca = run_detectors(df, X)
    df = score_suspicion(df)
    df = compute_btc_contamination(df)
    df = attach_validation(df)
    manifest = write_artifacts(df, pca)

    print("=" * 60)
    print("Pipeline complete. Artifacts written to ./artifacts/")
    print("=" * 60)
    for k, v in manifest.items():
        print(f"  {k:32s} {v}")
    print()
    print("Top 15 tokens by suspicion_score:")
    cols = ["token_symbol", "consensus_votes", "suspicion_score", "taxonomy"]
    print(df.sort_values("suspicion_score", ascending=False).head(15)[cols].to_string(index=False))


if __name__ == "__main__":
    main()
