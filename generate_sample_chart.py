import matplotlib.pyplot as plt
import seaborn as sns

labels = ['Confirmed Fraud / Exploit (e.g. YODA, SURGE, DFED)', 'Legitimate Protocol Outlier (e.g. 3Crv, MIM)', 'Undetermined / Missing Data']
sizes = [6, 2, 2] # Representative sampling of the Top 10 High Confidence Anomalies
colors = ['#e74c3c', '#2ecc71', '#f1c40f']

plt.figure(figsize=(9, 6))
plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140, explode=(0.1, 0, 0))
plt.title("Sample Verification of Top 10 Unsupervised Anomalies")
plt.tight_layout()
plt.savefig('fraud_validation_chart.png', dpi=300)
print("Saved sample validation chart.")
