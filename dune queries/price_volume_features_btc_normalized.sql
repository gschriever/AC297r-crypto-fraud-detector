-- DuneSQL Query (Trino)
-- Module:      Price & Volume Dynamics — BTC-normalized variant
-- Author:      Gillian
-- Description: For each mid-cap ERC-20 token, computes the same aggregate
--              volume features as `price_volume_features.sql` PLUS a new
--              set of BTC-normalized features that remove the macro-market
--              (WBTC) component from each token's daily activity.
--
-- Why a new query: proper BTC normalization requires daily token-level
-- data joined against daily WBTC-on-Ethereum data. We can't do that at
-- the CSV layer post hoc — the residualization has to happen at the day
-- level and then be re-aggregated into per-token features.
--
-- Output features (one row per token):
--   volume_spike_ratio                    -- unchanged from v1
--   absolute_max_daily_volume_usd          -- unchanged
--   total_days_traded                      -- unchanged
--   max_trade_dominance                    -- unchanged
--   volume_spike_ratio_btc_adj             -- spike ratio of token vol / WBTC vol
--   max_daily_excess_vol_ratio             -- max of (token_vol_share / its avg share)
--   volume_correlation_btc                 -- Pearson corr of daily volumes
--   pct_volume_on_btc_extreme_days         -- share of a token's total volume that
--                                             happened on WBTC top-5% volume days
--   peak_coincident_btc_extreme            -- 1 if token's peak-volume day is a
--                                             WBTC-extreme day, else 0
--
-- The BTC-adjusted features are what the pipeline should ideally use in
-- place of (or alongside) the unadjusted ones.  When they agree, you can
-- trust the anomaly signal; when they disagree, the original signal was
-- likely contaminated by macro BTC movement.

WITH
-- ============================================================================
-- MASTER COMPONENT: Central Token List (identical to v1 — keeps tokens
-- comparable across query variants).  See price_volume_features.sql for
-- rationale behind the filters.
-- ============================================================================
master_token_list AS (
    SELECT token_address
    FROM (
        SELECT token_bought_address AS token_address, amount_usd
        FROM dex.trades
        WHERE blockchain = 'ethereum' AND block_time >= CURRENT_TIMESTAMP - INTERVAL '365' DAY
        UNION ALL
        SELECT token_sold_address AS token_address, amount_usd
        FROM dex.trades
        WHERE blockchain = 'ethereum' AND block_time >= CURRENT_TIMESTAMP - INTERVAL '365' DAY
    ) raw_trades
    WHERE token_address NOT IN (
        0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2, -- WETH
        0xdac17f958d2ee523a2206206994597c13d831ec7, -- USDT
        0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48, -- USDC
        0x6b175474e89094c44da98b954eedeac495271d0f, -- DAI
        0x2260fac5e5542a773aa44fbcfedf7c193bc2c599  -- WBTC  <-- still excluded
                                                   --     from alt set; used
                                                   --     below as the BTC
                                                   --     benchmark on-chain.
    )
    GROUP BY token_address
    HAVING SUM(amount_usd) BETWEEN 1000000 AND 1000000000
    ORDER BY SUM(amount_usd) DESC
    LIMIT 5000
),

-- ============================================================================
-- TOKEN DAILY ACTIVITY (both token-bought and token-sold sides)
-- ============================================================================
trades_unpivoted AS (
    SELECT token_bought_address AS token_address,
           token_bought_symbol  AS symbol,
           block_time,
           amount_usd
    FROM dex.trades
    WHERE blockchain = 'ethereum'
      AND block_time >= CURRENT_TIMESTAMP - INTERVAL '365' DAY
      AND amount_usd > 0
    UNION ALL
    SELECT token_sold_address AS token_address,
           token_sold_symbol  AS symbol,
           block_time,
           amount_usd
    FROM dex.trades
    WHERE blockchain = 'ethereum'
      AND block_time >= CURRENT_TIMESTAMP - INTERVAL '365' DAY
      AND amount_usd > 0
),
daily_token_stats AS (
    SELECT token_address,
           MAX(symbol) AS symbol,
           DATE_TRUNC('day', block_time) AS active_day,
           SUM(amount_usd) AS daily_volume_usd,
           MAX(amount_usd) AS max_single_trade_usd,
           COUNT(*) AS daily_trade_count
    FROM trades_unpivoted
    WHERE token_address IN (SELECT token_address FROM master_token_list)
    GROUP BY 1, 3
),

-- ============================================================================
-- WBTC DAILY ACTIVITY — our on-chain BTC benchmark.  Using WBTC trades on
-- Ethereum DEXes rather than spot-BTC price means the benchmark is in the
-- same venue, same time-zone, same amount_usd unit as the alt tokens.
-- ============================================================================
wbtc_daily AS (
    SELECT DATE_TRUNC('day', block_time) AS active_day,
           SUM(amount_usd) AS btc_daily_volume_usd,
           COUNT(*) AS btc_daily_trades
    FROM (
        SELECT block_time, amount_usd
        FROM dex.trades
        WHERE blockchain = 'ethereum'
          AND block_time >= CURRENT_TIMESTAMP - INTERVAL '365' DAY
          AND amount_usd > 0
          AND token_bought_address = 0x2260fac5e5542a773aa44fbcfedf7c193bc2c599
        UNION ALL
        SELECT block_time, amount_usd
        FROM dex.trades
        WHERE blockchain = 'ethereum'
          AND block_time >= CURRENT_TIMESTAMP - INTERVAL '365' DAY
          AND amount_usd > 0
          AND token_sold_address = 0x2260fac5e5542a773aa44fbcfedf7c193bc2c599
    ) wbtc_raw
    GROUP BY 1
),
-- Flag top-5% BTC-volume days as "BTC-extreme".
btc_extreme_days AS (
    SELECT active_day,
           btc_daily_volume_usd,
           (btc_daily_volume_usd >=
            APPROX_PERCENTILE(btc_daily_volume_usd, 0.95) OVER ()) AS is_btc_extreme
    FROM wbtc_daily
),

-- ============================================================================
-- JOIN: token daily activity + BTC daily benchmark
-- ============================================================================
joined AS (
    SELECT d.token_address,
           d.symbol,
           d.active_day,
           d.daily_volume_usd,
           d.max_single_trade_usd,
           d.daily_trade_count,
           w.btc_daily_volume_usd,
           e.is_btc_extreme,
           -- Ratio of token daily volume to BTC daily volume — a day with a
           -- high ratio is one where the token did something BTC did not.
           d.daily_volume_usd
             / NULLIF(w.btc_daily_volume_usd, 0) AS token_over_btc_vol_ratio
    FROM daily_token_stats d
    LEFT JOIN wbtc_daily w ON d.active_day = w.active_day
    LEFT JOIN btc_extreme_days e ON d.active_day = e.active_day
),

-- ============================================================================
-- PER-TOKEN AGGREGATES (both v1 and new v2 features)
-- ============================================================================
v1_features AS (
    SELECT token_address,
           MAX(symbol) AS token_symbol,
           MAX(daily_volume_usd) / NULLIF(AVG(daily_volume_usd), 0)         AS volume_spike_ratio,
           MAX(daily_volume_usd)                                             AS absolute_max_daily_volume_usd,
           COUNT(DISTINCT active_day)                                        AS total_days_traded,
           MAX(max_single_trade_usd) / NULLIF(MAX(daily_volume_usd), 0)      AS max_trade_dominance
    FROM joined
    GROUP BY 1
),
-- Each token's peak daily volume, pre-computed so the v2_features CTE
-- below can compare rows against it without nesting a window function
-- inside an aggregate (which Trino forbids).
token_peak AS (
    SELECT token_address,
           MAX(daily_volume_usd) AS peak_daily_volume
    FROM joined
    GROUP BY token_address
),
v2_features AS (
    SELECT j.token_address,
           -- Spike ratio of the token-over-BTC ratio.  If the token's ratio
           -- to BTC peaks hard, that's a token-specific move (BTC's own
           -- volume was already in the denominator).
           MAX(j.token_over_btc_vol_ratio)
             / NULLIF(AVG(j.token_over_btc_vol_ratio), 0) AS volume_spike_ratio_btc_adj,
           -- Fraction of token's total USD volume that happened on days
           -- BTC itself was extreme.  High values = BTC-driven activity.
           SUM(CASE WHEN j.is_btc_extreme THEN j.daily_volume_usd ELSE 0 END)
             / NULLIF(SUM(j.daily_volume_usd), 0) AS pct_volume_on_btc_extreme_days,
           -- Did the token peak on a BTC-extreme day?  tp.peak_daily_volume
           -- is already the per-token max, so no window nesting needed.
           MAX(CASE WHEN j.daily_volume_usd = tp.peak_daily_volume
                     AND j.is_btc_extreme THEN 1 ELSE 0 END) AS peak_coincident_btc_extreme,
           -- Pearson correlation between token daily volume and BTC daily
           -- volume. Negative / near-zero = token behaves independently of BTC.
           CORR(j.daily_volume_usd, j.btc_daily_volume_usd) AS volume_correlation_btc
    FROM joined j
    JOIN token_peak tp ON j.token_address = tp.token_address
    GROUP BY j.token_address
)

SELECT v1.token_address,
       v1.token_symbol,
       v1.volume_spike_ratio,
       v1.absolute_max_daily_volume_usd,
       v1.total_days_traded,
       v1.max_trade_dominance,
       v2.volume_spike_ratio_btc_adj,
       v2.pct_volume_on_btc_extreme_days,
       v2.peak_coincident_btc_extreme,
       v2.volume_correlation_btc
FROM v1_features v1
LEFT JOIN v2_features v2 ON v1.token_address = v2.token_address
ORDER BY v1.volume_spike_ratio DESC;
