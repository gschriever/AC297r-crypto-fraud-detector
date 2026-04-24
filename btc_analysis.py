"""
BTC regime characterization for the 365-day study window.

Takes artifacts/btc_daily.csv (CryptoCompare OHLCV) and produces a small
summary + a plot showing when BTC moved a lot. Tokens whose peak-volume
day coincides with a BTC-extreme day are a priori suspect of having a
BTC-driven signal rather than a token-specific one.

This is a descriptive tool. It does NOT modify the validation pipeline —
that comes later, once daily token data is available from a re-run of
the modified Dune SQL (see sql/price_volume_features_btc_normalized.sql).
"""

from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts"


def main():
    btc = pd.read_csv(ARTIFACTS / "btc_daily.csv", parse_dates=["date"])
    btc = btc.dropna(subset=["log_ret"]).sort_values("date").reset_index(drop=True)

    btc["abs_ret_z"] = (btc["abs_log_ret"] - btc["abs_log_ret"].mean()) / btc["abs_log_ret"].std()
    btc["log_vol"] = np.log(btc["volume_usd"])
    btc["vol_z"] = (btc["log_vol"] - btc["log_vol"].mean()) / btc["log_vol"].std()

    ret_thresh = btc["abs_log_ret"].quantile(0.95)
    vol_thresh = btc["volume_usd"].quantile(0.95)
    btc["extreme_return"] = btc["abs_log_ret"] >= ret_thresh
    btc["extreme_volume"] = btc["volume_usd"] >= vol_thresh
    btc["btc_extreme"] = btc["extreme_return"] | btc["extreme_volume"]

    print("=" * 64)
    print("BTC regime during our 365-day Dune window")
    print("=" * 64)
    print(f"  Days observed:                  {len(btc)}")
    print(f"  Price range:                    ${btc.close.min():,.0f} -> ${btc.close.max():,.0f}")
    print(f"  Max single-day log-return:      {btc.log_ret.max():+.3f}  ({btc.loc[btc.log_ret.idxmax(),'date'].date()})")
    print(f"  Min single-day log-return:      {btc.log_ret.min():+.3f}  ({btc.loc[btc.log_ret.idxmin(),'date'].date()})")
    print(f"  Days with |return| >= p95:      {int(btc.extreme_return.sum())}  (threshold {ret_thresh:.3f})")
    print(f"  Days with volume >= p95:        {int(btc.extreme_volume.sum())}  (threshold ${vol_thresh:,.0f})")
    print(f"  Unique BTC-extreme days:        {int(btc.btc_extreme.sum())}  ({100*btc.btc_extreme.mean():.1f}% of window)")
    print()
    print("BTC volume-spike ratio (max / mean):   "
          f"{btc.volume_usd.max() / btc.volume_usd.mean():.2f}")
    print("This is the BENCHMARK: any alt token whose spike ratio is")
    print("barely higher than BTC's is likely inheriting BTC's movement,")
    print("not exhibiting token-specific behavior.")
    print()

    # Plot: BTC price + volume, with extreme days highlighted
    fig, axes = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
    axes[0].plot(btc["date"], btc["close"], color="#1f77b4", linewidth=1.3)
    axes[0].scatter(btc.loc[btc.btc_extreme, "date"], btc.loc[btc.btc_extreme, "close"],
                    color="#c0392b", s=28, zorder=3, label="BTC-extreme day (p95 return or volume)")
    axes[0].set_ylabel("BTC close (USD)")
    axes[0].set_title("BTC during the 365-day Dune window")
    axes[0].legend(loc="upper left")
    axes[0].grid(alpha=0.3)

    axes[1].bar(btc["date"], btc["volume_usd"] / 1e9, color="#95a5a6", width=1.0)
    axes[1].bar(btc.loc[btc.extreme_volume, "date"],
                btc.loc[btc.extreme_volume, "volume_usd"] / 1e9,
                color="#c0392b", width=1.0)
    axes[1].set_ylabel("BTC volume ($B)")
    axes[1].set_xlabel("Date")
    axes[1].grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(ARTIFACTS / "btc_regime.png", dpi=200)
    plt.close(fig)

    # Save the BTC-extreme date list — the most useful output for matching
    # against token spike dates (once we have daily token data).
    extreme = btc[btc.btc_extreme][["date", "log_ret", "volume_usd", "extreme_return", "extreme_volume"]].copy()
    extreme.to_csv(ARTIFACTS / "btc_extreme_days.csv", index=False)
    print(f"Top BTC-extreme days (by |return| or volume):")
    extreme["date"] = extreme["date"].dt.date
    print(extreme.sort_values("log_ret", key=abs, ascending=False).head(10).to_string(index=False))
    print()
    print(f"Artifacts written:")
    print(f"  artifacts/btc_daily.csv")
    print(f"  artifacts/btc_extreme_days.csv  ({len(extreme)} rows)")
    print(f"  artifacts/btc_regime.png")


if __name__ == "__main__":
    main()
