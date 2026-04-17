import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.cluster import DBSCAN
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from scipy.spatial.distance import mahalanobis
import warnings
warnings.filterwarnings('ignore')

csv_path = "Gillian_Price_and_Volume_Dynamic_Query_with_Token_Boundary_Conditions_QUERY_EXPORT.csv"
df = pd.read_csv(csv_path)

features = ['volume_spike_ratio', 'absolute_max_daily_volume_usd', 'total_days_traded', 'max_trade_dominance']
df[features] = df[features].apply(pd.to_numeric, errors='coerce')
df = df.dropna(subset=features).copy()

X = df[features].values
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

iso = IsolationForest(contamination=0.05, random_state=42)
df['iso_flag'] = iso.fit_predict(X_scaled) == -1
df['iso_score'] = iso.decision_function(X_scaled)

dbscan = DBSCAN(eps=1.5, min_samples=10)
df['dbscan_flag'] = dbscan.fit_predict(X_scaled) == -1

pca = PCA(n_components=2)
X_pca = pca.fit_transform(X_scaled)

cov_matrix = np.cov(X_pca, rowvar=False)
inv_cov_matrix = np.linalg.inv(cov_matrix)
center = np.mean(X_pca, axis=0)

distances = [mahalanobis(row, center, inv_cov_matrix) for row in X_pca]
df['mahalanobis_dist'] = distances
threshold = np.percentile(distances, 95)
df['pca_flag'] = df['mahalanobis_dist'] > threshold

df['anomaly_votes'] = df['iso_flag'].astype(int) + df['dbscan_flag'].astype(int) + df['pca_flag'].astype(int)

one_vote = df[df['anomaly_votes'] == 1].sort_values('iso_score')
print(one_vote['token_symbol'].dropna().head(10).tolist())
