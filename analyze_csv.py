import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import IsolationForest

# Read the data
csv_path = "Gillian_Price_and_Volume_Dynamic_Query_with_Token_Boundary_Conditions_QUERY_EXPORT.csv"
df = pd.read_csv(csv_path)

# Ensure columns are numeric and drop severely broken rows
features = ['volume_spike_ratio', 'absolute_max_daily_volume_usd', 'total_days_traded', 'max_trade_dominance']
df[features] = df[features].apply(pd.to_numeric, errors='coerce')
df = df.dropna(subset=features)

print("====== SUMMARY STATISTICS ======")
print(df[features].describe().T)

print("\n====== FITTING ISOLATION FOREST ======")
# Fit an unsupervised Isolation Forest model just to test the data!
iso = IsolationForest(contamination=0.01, random_state=42) # Assuming 1% are severe anomalies
df['anomaly_score'] = iso.fit_predict(df[features])
# IsolationForest outputs -1 for anomalies, 1 for inliers. We can also get raw scores:
df['anomaly_magnitude'] = iso.decision_function(df[features])

anomalies = df[df['anomaly_score'] == -1].sort_values('anomaly_magnitude').head(10)

print("\nTop 10 Most Anomalous Tokens (according to Isolation Forest):")
for _, row in anomalies.iterrows():
    print(f"Token: {row.get('token_symbol', 'N/A')} ({row['token_address']})")
    print(f"  Spike Ratio: {row['volume_spike_ratio']:.2f}x")
    print(f"  Max Trade Dominance: {row['max_trade_dominance'] * 100:.1f}%")
    print(f"  Days Traded: {row['total_days_traded']}")
    print(f"  Max Vol USD: ${row['absolute_max_daily_volume_usd']:,.0f}")
    print("---")

print("\n====== GENERATING VISUALIZATIONS ======")

sns.set_theme(style="darkgrid")

# Plot 1: Scatter plot of Volume Spike Ratio vs Days Traded
plt.figure(figsize=(10, 6))
# Plot normal data
sns.scatterplot(
    data=df[df['anomaly_score'] == 1], 
    x='total_days_traded', 
    y='volume_spike_ratio', 
    alpha=0.3, 
    color='blue',
    label='Normal Tokens'
)
# Plot anomalies
sns.scatterplot(
    data=df[df['anomaly_score'] == -1], 
    x='total_days_traded', 
    y='volume_spike_ratio', 
    alpha=0.9, 
    color='red', 
    s=100,
    label='Anomalies (Fraud Risks)'
)

# Annotate the top 5 anomalies
for i, row in df[df['anomaly_score'] == -1].sort_values('anomaly_magnitude').head(5).iterrows():
    plt.annotate(row.get('token_symbol', 'Unknown'), 
                 (row['total_days_traded'], row['volume_spike_ratio']),
                 xytext=(5, 5), textcoords='offset points', color='darkred', weight='bold')

plt.title('Isolation Forest Anomaly Detection: Volume Spike vs Activity Lifespan')
plt.xlabel('Total Days Traded')
plt.ylabel('Volume Spike Ratio (Max / Avg Daily Volume)')
plt.yscale('log') # Log scale because spikes are so extreme
plt.legend()
plt.tight_layout()
plt.savefig('anomaly_scatter_plot.png', dpi=300)
print("Saved anomaly_scatter_plot.png")

# Plot 2: Max Trade Dominance Distribution
plt.figure(figsize=(10, 6))
sns.histplot(df['max_trade_dominance'] * 100, bins=50, kde=True, color='purple')
plt.title('Distribution of Max Single-Trade Dominance')
plt.xlabel('% of Daily Volume from a Single Trade')
plt.ylabel('Frequency')
plt.tight_layout()
plt.savefig('trade_dominance_distribution.png', dpi=300)
print("Saved trade_dominance_distribution.png")

print("Analysis Complete.")
