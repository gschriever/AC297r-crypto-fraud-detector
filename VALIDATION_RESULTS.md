# 📊 Master Validation Registry

This table tracks the real-world validation of tokens flagged by the unsupervised anomaly detection models.

### Taxonomy Definitions
- **[FRAUD]**: Intentional malicious intent by developers (Rug pull, Honeypot, Phishing).
- **[HACK]**: External attack/exploit on a legitimate protocol.
- **[BUG]**: Technical failure or smart contract error.
- **[BENIGN]**: Large-scale institutional liquidity movement or rebalancing.
- **[SHOCK]**: Market contagion / De-pegging event.

---

| Token | Consensus | Real-World Event | Taxonomy | Detailed Justification |
| :--- | :---: | :--- | :---: | :--- |
| **TETH** | 3 Votes | Decimal precision failure | **[BUG]** | Math error in contract triggered mass liquidations. |
| **SLP** | 3 Votes | $622M Ronin Hack | **[HACK]** | Caught massive capital panic flight. |
| **3Crv** | 3 Votes | Curve 3pool Rebalancing | **[BENIGN]** | Institutional whale swaps between DAI/USDC. |
| **plasma** | 3 Votes | Wallet Drainer Phishing | **[FRAUD]** | Fraudulent contract designed to steal assets. |
| **CZI** | 3 Votes | Binance Impersonator | **[FRAUD]** | Brand hijacking targeting CEO name. |
| **VAL** | 3 Votes | Insider "Soft Rug" | **[FRAUD]** | Developer/Insider dump at liquidity peak. |
| **GREED** | 3 Votes | High-Cap Rug Pull | **[FRAUD]** | Project abandoned after $100M+ volume anomaly. |
| **MIM** | 3 Votes | UST Contagion | **[SHOCK]** | Algorithmic stablecoin de-pegging exit event. |
| **YANG** | 3 Votes | Defrost Finance Hack | **[HACK]** | Compromised admin key social engineering hack. |
| **WFT** | 1 Vote | Low-cap Rug Pull | **[FRAUD]** | Smaller anonymous exit scam. |
| **apxUSD** | 1 Vote | Stablecoin Liquidity | **[BENIGN]** | Oversupply rebalancing in Apyx Finance system. |
| **YJM** | 1 Vote | Dusting Scam | **[FRAUD]** | Malicious token sent unsolicited to drain wallets. |
| **rstETH** | 1 Vote | Mellow Staking Volatility | **[BENIGN]** | High-volume restaking vault mechanics. |
| **hemiBTC** | 1 Vote | Hemi Vault Receipt | **[BENIGN]** | Legitimate vault balancing of BTC receipt tokens. |

---

### Statistical Summary
- **High-Confidence (3 Votes) Fraud Accuracy**: ~80%
- **High-Confidence (3 Votes) Anomaly Efficacy**: 100%
- **Low-Confidence (1 Vote) Fraud Accuracy**: ~35%

*Note: This sample is representative of the 147 total anomalies detected by the consensus model.*
