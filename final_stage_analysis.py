import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from sklearn.ensemble import IsolationForest
from sklearn.cluster import DBSCAN
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from scipy.spatial.distance import mahalanobis
import warnings

warnings.filterwarnings('ignore')

# 1. Load and Merge Data
print("Loading datasets...")
base_df = pd.read_csv("Gillian_Price_and_Volume_Dynamic_Query_with_Token_Boundary_Conditions_QUERY_EXPORT.csv")
temporal_df = pd.read_csv("dune queries/Temporal_Price_Volume_Dynamics_24h_Window_Extraction.csv")

# Merge on token_address
df = pd.merge(base_df, temporal_df, on="token_address", how="inner")

# Select final features (including the "Do Not Rug on Me" 24h metrics)
features = [
    'volume_spike_ratio', 
    'absolute_max_daily_volume_usd', 
    'max_trade_dominance',
    'early_velocity_ratio',
    'early_trade_dominance'
]

# Clean data
df[features] = df[features].apply(pd.to_numeric, errors='coerce')
df = df.dropna(subset=features).copy()
X = df[features].values
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 2. Consensus Modeling
print("Generating Anomaly Consensus...")
# Isolation Forest
iso = IsolationForest(contamination=0.05, random_state=42)
df['iso_flag'] = iso.fit_predict(X_scaled) == -1
df['iso_score'] = iso.decision_function(X_scaled)

# DBSCAN
dbscan = DBSCAN(eps=1.5, min_samples=10)
df['dbscan_flag'] = dbscan.fit_predict(X_scaled) == -1

# PCA + Mahalanobis
pca_model = PCA(n_components=2)
X_pca = pca_model.fit_transform(X_scaled)
cov_matrix = np.cov(X_pca, rowvar=False)
inv_cov_matrix = np.linalg.inv(cov_matrix)
center = np.mean(X_pca, axis=0)
distances = [mahalanobis(row, center, inv_cov_matrix) for row in X_pca]
df['pca_flag'] = np.array(distances) > np.percentile(distances, 95)

# Consensus Voting
df['consensus_votes'] = df['iso_flag'].astype(int) + df['dbscan_flag'].astype(int) + df['pca_flag'].astype(int)

# 3. Create "Scam Probability" Score (Refined using 24h Velocity)
# Higher weight given to early velocity ratio as per "Do Not Rug on Me"
df['scam_probability'] = (
    (df['consensus_votes'] / 3.0) * 0.5 + 
    (df['early_velocity_ratio'] / df['early_velocity_ratio'].max()) * 0.3 +
    (df['max_trade_dominance'] / df['max_trade_dominance'].max()) * 0.2
) * 100

# 4. STATIC VISUALIZATION (for Poster)
print("Creating Static Anomaly Map...")
plt.figure(figsize=(14, 10))
sns.set_style("whitegrid")
scatter = sns.scatterplot(
    x=X_pca[:, 0], y=X_pca[:, 1], 
    hue=df['consensus_votes'], 
    palette="viridis",
    size=df['scam_probability'],
    sizes=(20, 200),
    alpha=0.6,
    edgecolor="none"
)

# Highlight and Label key story tokens
annotations = {
    'TETH': 'Protocol Bug',
    'SLP': 'Ronin Hack',
    '3Crv': 'Institutional Rebalancing',
    'plasma': 'Phishing Drainer',
    'CZI': 'Binance Impersonator',
    'GREED': 'Exit Scam',
    'MIM': 'UST Contagion'
}

for i, row in df.iterrows():
    if row['token_symbol'] in annotations:
        plt.annotate(
            f"{row['token_symbol']}\n({annotations[row['token_symbol']]})",
            (X_pca[i, 0], X_pca[i, 1]),
            textcoords="offset points",
            xytext=(10,10),
            ha='center',
            fontsize=9,
            fontweight='bold',
            bbox=dict(boxstyle='round,pad=0.3', fc='white', alpha=0.5)
        )

plt.title("CAPSTONE ANOMALY MAP: Consensus Severity and Failure Modes", fontsize=16)
plt.xlabel("PCA Component 1 (Volume Dynamics)", fontsize=12)
plt.ylabel("PCA Component 2 (Temporal Velocity)", fontsize=12)
plt.legend(title="Consensus Votes", bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.savefig("anomaly_map_static.png", dpi=300)
plt.close()

# 5. DYNAMIC VISUALIZATION (for Live Demo/PPT)
print("Creating Interactive Anomaly Dashboard...")
df['PCA1'] = X_pca[:, 0]
df['PCA2'] = X_pca[:, 1]
fig = px.scatter(
    df, x="PCA1", y="PCA2",
    color="consensus_votes",
    size="scam_probability",
    hover_name="token_symbol",
    hover_data=["early_velocity_ratio", "max_trade_dominance", "total_days_traded"],
    color_continuous_scale="Viridis",
    title="Interactive Scam Consensus Dashboard (Hover to Explore)",
    labels={"consensus_votes": "Votes"}
)
fig.write_html("anomaly_map_interactive.html")

print("Analysis Complete!")
print(f"Static Map: anomaly_map_static.png")
print(f"Interactive Map: anomaly_map_interactive.html")

# Output top 10 temporal anomalies for manual check
print("\n--- TOP TEMPORAL ANOMALIES (High early velocity) ---")
top_temporal = df.sort_values('early_velocity_ratio', ascending=False).head(10)
for _, row in top_temporal.iterrows():
    print(f"Token: {row['token_symbol']} | 24h Volume Ratio: {row['early_velocity_ratio']*100:.1f}% | Votes: {row['consensus_votes']}")
