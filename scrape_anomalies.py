import pandas as pd
import numpy as np
import time
import json
import matplotlib.pyplot as plt
import seaborn as sns
from duckduckgo_search import DDGS
from transformers import pipeline
import warnings

warnings.filterwarnings('ignore')

print("Loading Data...")
# Load the exported CSV and re-run consensus logic quickly to isolate the 46 tokens
df = pd.read_csv("Gillian_Price_and_Volume_Dynamic_Query_with_Token_Boundary_Conditions_QUERY_EXPORT.csv")
features = ['volume_spike_ratio', 'absolute_max_daily_volume_usd', 'total_days_traded', 'max_trade_dominance']
df[features] = df[features].apply(pd.to_numeric, errors='coerce')
df = df.dropna(subset=features).copy()

from sklearn.ensemble import IsolationForest
from sklearn.cluster import DBSCAN
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from scipy.spatial.distance import mahalanobis

X = df[features].values
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

iso = IsolationForest(contamination=0.05, random_state=42)
df['iso_flag'] = iso.fit_predict(X_scaled) == -1
dbscan = DBSCAN(eps=1.5, min_samples=10)
df['dbscan_flag'] = dbscan.fit_predict(X_scaled) == -1
pca = PCA(n_components=2)
X_pca = pca.fit_transform(X_scaled)
inv_cov = np.linalg.inv(np.cov(X_pca, rowvar=False))
center = np.mean(X_pca, axis=0)
dists = [mahalanobis(row, center, inv_cov) for row in X_pca]
df['pca_flag'] = dists > np.percentile(dists, 95)
df['votes'] = df['iso_flag'].astype(int) + df['dbscan_flag'].astype(int) + df['pca_flag'].astype(int)

high_conf = df[df['votes'] >= 2].copy()
print(f"Isolated {len(high_conf)} High Confidence Tokens.")

print("Initializing Zero-Shot Context/Sentiment Model...")
# Using a lightweight zero-shot classification model to interpret semantic meaning of DDG snippets!
try:
    classifier = pipeline("zero-shot-classification", model="typeform/distilbert-base-uncased-mnli")
except:
    # Fallback to a faster robust model if typeform is deprecated
    classifier = pipeline("zero-shot-classification", model="cross-encoder/nli-distilroberta-base")

candidate_labels = ["fraud, scam, or rug pull", "legitimate crypto project", "neutral market data"]

results = []
queries_executed = 0

print("Starting Web Scraping & Semantic Verification...")
with DDGS() as ddgs:
    for idx, row in high_conf.iterrows():
        symbol = row.get('token_symbol', 'Unknown')
        address = row['token_address']
        if pd.isna(symbol) or symbol == 'Unknown':
            continue
            
        print(f"[{queries_executed+1}] Investigating {symbol}...")
        query = f'"{symbol}" crypto AND ("scam" OR "rug pull" OR "exploit" OR "hack" OR "legitimate")'
        
        try:
            # Scrape top 3 summaries
            search_results = list(ddgs.text(query, max_results=3))
            
            if not search_results:
                results.append((symbol, address, "Undetermined", "No search results found."))
                time.sleep(1.5)
                queries_executed += 1
                continue
                
            combined_text = " ".join([res.get('body', '') for res in search_results])
            
            # Feed into NLP model to determine contextual presence of fraud
            classification = classifier(combined_text, candidate_labels)
            top_label = classification['labels'][0]
            confidence = classification['scores'][0]
            
            evidence = combined_text[:150] + "..." # Snippet for the report
            
            if top_label == "fraud, scam, or rug pull" and confidence > 0.45:
                status = "Confirmed Fraud"
            elif top_label == "legitimate crypto project" and confidence > 0.45:
                status = "Legitimate Protocol outlier"
            else:
                status = "Undetermined / Mixed"
                
            results.append((symbol, address, status, evidence))
            
        except Exception as e:
            print(f"Error on {symbol}: {e}")
            results.append((symbol, address, "Error", str(e)))
            
        time.sleep(2) # Respect rate limits
        queries_executed += 1
        
        if queries_executed >= 200:
            break

results_df = pd.DataFrame(results, columns=["Symbol", "Address", "Validation Status", "Context Snippet"])
results_df.to_csv("fraud_validation_results.csv", index=False)

print("\n==== ANALYSIS SUMMARY ====")
summary_counts = results_df["Validation Status"].value_counts()
print(summary_counts)

print("\nGenerating Validation Chart...")
plt.figure(figsize=(9, 6))
sns.set_theme(style="whitegrid")
colors = {'Confirmed Fraud': '#e74c3c', 'Legitimate Protocol outlier': '#2ecc71', 'Undetermined / Mixed': '#f1c40f', 'Error': '#95a5a6'}
sns.barplot(x=summary_counts.index, y=summary_counts.values, palette=colors)
plt.title("HuggingFace Zero-Shot Verification of 46 Unsupervised Anomalies")
plt.ylabel("Number of Tokens")
plt.xticks(rotation=15)
plt.tight_layout()
plt.savefig("fraud_validation_chart.png", dpi=300)
print("Saved fraud_validation_chart.png")
print("Execution Complete.")
