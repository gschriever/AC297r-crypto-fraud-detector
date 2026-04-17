import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

# Hardcoded data from the user's Dune Analytics screenshot
data = {
    'Token': ['MIM', 'LUFFY', '3Crv', 'ALPA', 'OM', 'SLP', 'AJNA', 'CERE', 'MIND', 'DFI'],
    'Volume Spike Ratio': [326.9, 315.8, 309.7, 291.5, 286.8, 273.1, 272.2, 268.2, 266.8, 260.7]
}
df = pd.DataFrame(data)

# Set the style
plt.figure(figsize=(10, 6))
sns.set_theme(style="whitegrid")

# Create a bar plot
ax = sns.barplot(x='Volume Spike Ratio', y='Token', data=df, palette='viridis')

# Add labels and title
plt.title('Top 10 Ethereum Tokens by Daily Volume Spike Ratio (Last 12 Months)', fontsize=14, pad=15)
plt.xlabel('Volume Spike Ratio (Max Daily Volume / Avg Daily Volume)', fontsize=12)
plt.ylabel('Token Symbol', fontsize=12)

# Add data labels to the bars
for i in ax.containers:
    ax.bar_label(i, padding=5, fmt='%.1f', fontsize=10)

# Adjust layout and save
plt.tight_layout()
plt.savefig('volume_spike_chart.png', dpi=300, bbox_inches='tight')
print("Successfully generated volume_spike_chart.png")
