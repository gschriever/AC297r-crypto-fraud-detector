"""
Layer 2 — P(fraud | suspicious).

Consumes artifacts/tokens_scored.csv and fits a logistic regression on the
n=14 hand-validated subset, mapping suspicious-behavior features to the
binary target `is_fraud`. The output is a per-token probability that the
flagged behavior is intentional developer fraud (FRAUD) as opposed to a
benign anomaly (HACK/BUG/BENIGN/SHOCK).

The validation set is tiny by design — this is a calibration layer, not a
classifier. Honest reporting: leave-one-out CV, with an explicit caveat on
the sample size in the accompanying slide.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import LeaveOneOut
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts"
SCORED = ARTIFACTS / "tokens_scored.csv"

# Features chosen to distinguish FRAUD (intentional rug/scam) from the other
# anomaly types (HACK/BUG/BENIGN/SHOCK) *given* a token is already flagged
# as suspicious by Layer 1. Layer-1's own output (suspicion_score) is
# deliberately excluded here — it measures "how anomalous" not "what kind
# of anomaly", and including it confounds the two layers.
CALIBRATION_FEATURES = [
    "total_days_traded",
    "max_trade_dominance",
    "early_velocity_ratio",
    "volume_spike_ratio",
]
# Heavier L2 regularization than default — n=14 makes the MLE unstable;
# shrinkage keeps extrapolations to the full 4k-token set from blowing up.
CALIBRATOR_C = 0.5


def fit_calibrator(validated: pd.DataFrame) -> tuple[LogisticRegression, StandardScaler, dict]:
    X = validated[CALIBRATION_FEATURES].to_numpy()
    y = validated["is_fraud"].to_numpy()

    scaler = StandardScaler().fit(X)
    X_scaled = scaler.transform(X)

    # Leave-one-out CV: the only honest estimate at n=14.
    loo = LeaveOneOut()
    preds = np.zeros_like(y, dtype=float)
    for train_idx, test_idx in loo.split(X_scaled):
        m = LogisticRegression(class_weight="balanced", max_iter=1000, C=CALIBRATOR_C)
        m.fit(X_scaled[train_idx], y[train_idx])
        preds[test_idx] = m.predict_proba(X_scaled[test_idx])[:, 1]

    loo_acc = float(((preds >= 0.5).astype(int) == y).mean())
    # Brier score — calibration quality, lower is better.
    brier = float(((preds - y) ** 2).mean())

    # Fit the final model on all validated data.
    model = LogisticRegression(class_weight="balanced", max_iter=1000, C=CALIBRATOR_C)
    model.fit(X_scaled, y)

    report = {
        "n_calibration": int(len(validated)),
        "n_fraud": int(y.sum()),
        "n_not_fraud": int(len(y) - y.sum()),
        "loo_accuracy": round(loo_acc, 3),
        "loo_brier": round(brier, 3),
        "loo_predictions": pd.DataFrame(
            {
                "token_symbol": validated["token_symbol"].values,
                "taxonomy": validated["taxonomy"].values,
                "is_fraud": y,
                "loo_p_fraud": preds.round(3),
            }
        ).sort_values("loo_p_fraud", ascending=False),
        "coefficients": dict(zip(CALIBRATION_FEATURES, model.coef_[0].round(3))),
        "intercept": round(float(model.intercept_[0]), 3),
    }
    return model, scaler, report


def apply_calibrator(
    df: pd.DataFrame,
    model: LogisticRegression,
    scaler: StandardScaler,
    feature_ranges: dict,
) -> pd.DataFrame:
    # P(fraud | suspicious) is only defined on the suspicious subset. We gate
    # on the continuous suspicion_score ≥ p90 (matches the Layer-1 headline
    # rule), not on the legacy discrete vote count. Also clip features to
    # calibration range to prevent extrapolation from producing absurd probs.
    X = df[CALIBRATION_FEATURES].copy()
    for f, (lo, hi) in feature_ranges.items():
        X[f] = X[f].clip(lower=lo, upper=hi)
    X_scaled = scaler.transform(X.to_numpy())
    probs = model.predict_proba(X_scaled)[:, 1]
    gate = df["suspicion_score"] >= df["suspicion_score"].quantile(0.90)
    df["p_fraud"] = np.where(gate, probs, np.nan)
    return df


def plot_calibration(report: dict, df: pd.DataFrame) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    loo = report["loo_predictions"]
    colors = ["#c0392b" if t == "FRAUD" else "#2980b9" for t in loo["taxonomy"]]
    axes[0].barh(loo["token_symbol"], loo["loo_p_fraud"], color=colors)
    axes[0].axvline(0.5, color="gray", linestyle="--", linewidth=1)
    axes[0].set_xlabel("Leave-one-out P(fraud)")
    axes[0].set_title(f"Calibration on validated subset (n={report['n_calibration']})")
    axes[0].set_xlim(0, 1)
    axes[0].invert_yaxis()

    flagged = df[df["consensus_votes"] >= 2].copy()
    axes[1].hist(flagged["p_fraud"], bins=30, color="#8e44ad", edgecolor="white")
    axes[1].set_xlabel("P(fraud | suspicious)")
    axes[1].set_ylabel("Count of ≥2-vote tokens")
    axes[1].set_title(f"P(fraud) distribution across {len(flagged)} flagged tokens")

    fig.suptitle(
        "Layer 2: fraud calibration  —  LOO accuracy "
        f"{report['loo_accuracy']:.2f}, Brier {report['loo_brier']:.2f}",
        fontsize=13,
    )
    fig.tight_layout()
    fig.savefig(ARTIFACTS / "calibration_report.png", dpi=300)
    plt.close(fig)


def main() -> None:
    df = pd.read_csv(SCORED)
    # Use only labeled tokens for calibration — drop UNKNOWN (held out).
    # Registry is address-keyed so no symbol-collision dedup is needed.
    validated = (
        df[(df["is_validated"] == 1) & (df["taxonomy"] != "UNKNOWN")]
        .dropna(subset=CALIBRATION_FEATURES)
        .reset_index(drop=True)
    )

    model, scaler, report = fit_calibrator(validated)
    feature_ranges = {
        f: (validated[f].min(), validated[f].max()) for f in CALIBRATION_FEATURES
    }
    df = apply_calibrator(df, model, scaler, feature_ranges)
    df.to_csv(ARTIFACTS / "tokens_calibrated.csv", index=False)

    plot_calibration(report, df)

    top = df.sort_values("p_fraud", ascending=False).head(15)
    top[["token_symbol", "consensus_votes", "suspicion_score", "p_fraud", "taxonomy"]].to_csv(
        ARTIFACTS / "top_fraud_candidates.csv", index=False
    )

    print("=" * 60)
    print("Calibration complete.")
    print("=" * 60)
    print(f"  n_calibration   : {report['n_calibration']}")
    print(f"  n_fraud         : {report['n_fraud']}")
    print(f"  LOO accuracy    : {report['loo_accuracy']}")
    print(f"  Brier score     : {report['loo_brier']}")
    print(f"  Intercept       : {report['intercept']}")
    print("  Coefficients (standardized):")
    for k, v in report["coefficients"].items():
        print(f"    {k:30s} {v:+.3f}")
    print()
    print("LOO predictions on validated subset:")
    print(report["loo_predictions"].to_string(index=False))
    print()
    print("Top 15 fraud candidates across full dataset:")
    print(top[["token_symbol", "consensus_votes", "suspicion_score", "p_fraud", "taxonomy"]].to_string(index=False))


if __name__ == "__main__":
    main()
