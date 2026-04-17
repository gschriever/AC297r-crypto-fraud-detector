-- DuneSQL Query (Trino)
-- Module: Price & Volume Dynamics (Static Feature Extraction)
-- Author: Gillian
-- Description: Extracts static price and volume features for unsupervised learning

WITH 
-- ==============================================================================
-- MASTER COMPONENT: Central Token List (Every teammate must use this exact CTE)
-- ==============================================================================
master_token_list AS (
    -- Gathers the top 5,000 mid-cap tokens across Ethereum DEXs over the last year.
    -- It excludes mega-cap stablecoins/Ethereum to isolate alt/mid-caps.
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
        0x2260fac5e5542a773aa44fbcfedf7c193bc2c599  -- WBTC
    )
    GROUP BY token_address
    -- Require at least $1M in yearly volume to filter out completely dead dust tokens
    -- Cap at $1B to exclude mega-caps to ensure we only target mid-caps
    HAVING SUM(amount_usd) BETWEEN 1000000 AND 1000000000
    ORDER BY SUM(amount_usd) DESC
    LIMIT 5000
),

-- ==============================================================================
-- GILLIAN'S MODULE: Price & Volume Feature Extraction
-- ==============================================================================
trades_unpivoted AS (
    SELECT 
        token_bought_address AS token_address,
        token_bought_symbol AS symbol,
        block_time,
        amount_usd
    FROM dex.trades
    WHERE blockchain = 'ethereum'
      AND block_time >= CURRENT_TIMESTAMP - INTERVAL '365' DAY
      AND amount_usd > 0
    
    UNION ALL
    
    SELECT 
        token_sold_address AS token_address,
        token_sold_symbol AS symbol,
        block_time,
        amount_usd
    FROM dex.trades
    WHERE blockchain = 'ethereum'
      AND block_time >= CURRENT_TIMESTAMP - INTERVAL '365' DAY
      AND amount_usd > 0
),
daily_token_stats AS (
    SELECT 
        token_address,
        MAX(symbol) AS symbol,
        DATE_TRUNC('day', block_time) AS active_day,
        SUM(amount_usd) AS daily_volume_usd,
        MAX(amount_usd) AS max_single_trade_usd,
        COUNT(*) AS daily_trade_count
    FROM trades_unpivoted
    -- FILTERING HAPPENS HERE: We only calculate stats for the Master 5,000 list
    WHERE token_address IN (SELECT token_address FROM master_token_list)
    GROUP BY 1, 3
),
STATIC_FEATURES AS (
    SELECT
        token_address,
        MAX(symbol) AS token_symbol,
        
        -- Feature 1: Volume Spike Ratio
        MAX(daily_volume_usd) / NULLIF(AVG(daily_volume_usd), 0) AS volume_spike_ratio,
        
        -- Feature 2: Peak Daily Volume
        MAX(daily_volume_usd) AS absolute_max_daily_volume_usd,
        
        -- Feature 3: Trading Density
        COUNT(DISTINCT active_day) AS total_days_traded,
        
        -- Feature 4: Max single trade dominance
        MAX(max_single_trade_usd) / NULLIF(MAX(daily_volume_usd), 0) AS max_trade_dominance

    FROM daily_token_stats
    GROUP BY 1
)

SELECT * 
FROM STATIC_FEATURES
-- We remove the LIMIT 100 at the end to ensure we output ALL 5,000 targeted tokens for merging
ORDER BY volume_spike_ratio DESC;
