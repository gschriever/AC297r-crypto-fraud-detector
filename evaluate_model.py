import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.cluster import DBSCAN
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from scipy.spatial.distance import mahalanobis
import warnings
warnings.filterwarnings('ignore')

# 1. Load Data
csv_path = "Gillian_Price_and_Volume_Dynamic_Query_with_Token_Boundary_Conditions_QUERY_EXPORT.csv"
df = pd.read_csv(csv_path)

features = ['volume_spike_ratio', 'absolute_max_daily_volume_usd', 'total_days_traded', 'max_trade_dominance']
df[features] = df[features].apply(pd.to_numeric, errors='coerce')
df = df.dropna(subset=features).copy()

# 2. Preprocessing
X = df[features].values
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 3. Model 1: Isolation Forest (5% Contamination as per Cecilia's notes)
iso = IsolationForest(contamination=0.05, random_state=42)
df['iso_flag'] = iso.fit_predict(X_scaled) == -1
df['iso_score'] = iso.decision_function(X_scaled)

# 4. Model 2: DBSCAN (eps=1.5, min_samples=10 as per notes)
dbscan = DBSCAN(eps=1.5, min_samples=10)
df['dbscan_flag'] = dbscan.fit_predict(X_scaled) == -1

# 5. Model 3: PCA + Mahalanobis Distance (top 5% threshold)
pca = PCA(n_components=2)
X_pca = pca.fit_transform(X_scaled)

cov_matrix = np.cov(X_pca, rowvar=False)
inv_cov_matrix = np.linalg.inv(cov_matrix)
center = np.mean(X_pca, axis=0)

distances = [mahalanobis(row, center, inv_cov_matrix) for row in X_pca]
df['mahalanobis_dist'] = distances
threshold = np.percentile(distances, 95)
df['pca_flag'] = df['mahalanobis_dist'] > threshold

# 6. Consensus Voting
df['anomaly_votes'] = df['iso_flag'].astype(int) + df['dbscan_flag'].astype(int) + df['pca_flag'].astype(int)

consensus_3 = df[df['anomaly_votes'] == 3]
consensus_2 = df[df['anomaly_votes'] >= 2]

print(f"Total tokens evaluated: {len(df)}")
print(f"Tokens flagged by >= 2 methods: {len(consensus_2)}")
print(f"Tokens flagged by all 3 methods: {len(consensus_3)}")

print("\n--- TOP CONSENSUS ANOMALIES (Flagged by all 3 methods) ---")
# Sort by isolation forest anomaly score (lowest score = most severe anomaly)
top_anomalies = consensus_3.sort_values('iso_score').head(15)

for _, row in top_anomalies.iterrows():
    print(f"Token: {row.get('token_symbol', 'Unknown')} | Address: {row['token_address']}")
    print(f"  Spike: {row['volume_spike_ratio']:.1f}x | Days Traded: {row['total_days_traded']} | Dominance: {row['max_trade_dominance']*100:.1f}%")
