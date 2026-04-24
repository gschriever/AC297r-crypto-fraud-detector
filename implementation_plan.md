# Final Stage Strategy: Unsupervised Pipeline Evolution

This plan outlines the final updates required to transition the project from a "v1 Prototype" to a "Final Capstone" project. The focus is on moving from discovery to explaining and optimizing the model.

## User Review Required

> [!IMPORTANT]
> **Data Access**: Some features (like Price Drawdown or Skewness) may require updating the DuneSQL query (`price_volume_features.sql`) and re-exporting the data. We should confirm if you have the ability to re-run this query on Dune before proceeding with Feature Augmentation.

## Phase 1: Temporal Enrichment ("The 24-Hour Window")
Based on the research from "Do Not Rug on Me," timing is critical. We will augment our features to capture the "Scam Velocity" in the first 24 hours of a token's life.
- **[MODIFY] [price_volume_features.sql](file:///Users/Gillian/Downloads/crypto%20project/price_volume_features.sql)**: Update query to extract features specific to the **First 24 Hours Post-Launch** (e.g., 24h volume spike, 24h trade dominance).
- **[MODIFY] [evaluate_model.py](file:///Users/Gillian/Downloads/crypto%20project/evaluate_model.py)**: Incorporate these temporal features into the anomaly consensus detection.

## Phase 2: Consensus Visualization ("The Anomaly Map")
We will create a flagship visualization that maps the entire token space and highlights the "Severity via Consensus" logic used in our PowerPoint.
- **[NEW] `visualize_consensus.py`**: A high-resolution scatter plot (PCA-reduced) where tokens are color-coded by their consensus level (1, 2, or 3 votes). This will serve as a visual "heatmap" for the final presentation.

## Phase 3: Explainability ("The SHAP Narrative")
To communicate findings clearly, we will use SHAP (Shapley values) to "decode" the results. 
- **Explainability Layer**: For each top anomaly, we will generate a "contribution plot" showing exactly which features (e.g., 24h Spike vs. Total Dominance) triggered the flag. 

### Phase 4: Final Presentation Reporting
- **Scam Probability Score**: Replace binary flag counts with a weighted probability score (0-100%).
- **Final Visualization**: A 3D scatter plot (using PCA) color-coded by the new Probability Score + manual validation labels.

## Open Questions

1. **Dune Strategy**: I am providing the updated SQL below. Once you run it, we can begin the "Temporal" phase.
2. **Visual Style**: Should the final consensus map be a high-res static plot (optimized for a PPT slide) or an interactive HTML file (better for a live demo)?

## Verification Plan

### Automated Tests
- Cross-validation against existing `VALIDATION_RESULTS.md` to ensure the "True Positive" rate increases with new features.
- SHAP value stability check.

### Manual Verification
- Visual inspection of the 3D anomaly clusters.
- Reviewing the "Top 5 Scams" flagged by the new weighted score.
