# Clustering — where we landed and why

Reference note for the poster. If the professor or a reviewer asks
"what about clustering?", this is the position we defend.

## Do we use clustering?

Yes — one of our three Layer-1 detectors is **DBSCAN** (Density-Based
Spatial Clustering of Applications with Noise). DBSCAN groups tokens
into dense neighborhoods in feature space and labels any token that
doesn't belong to any neighborhood as a "noise point." We treat noise
points as anomalies. So the clustering is there, it's just plugged into
an outlier-detection role rather than a "let's group tokens into K
behavioral types" role.

## Per-detector contribution on the 15 validated FRAUD tokens

| Detector | Fraud recall (alone) | NORMAL flag rate (alone) |
|---|---:|---:|
| Isolation Forest | **73%** (11/15) | 22% |
| PCA + Mahalanobis | 33% (5/15)  | 30% |
| **DBSCAN**       | **27%** (4/15)  | **14%** |

DBSCAN is the weakest single detector for recall and the most selective
for specificity. It misses 7 frauds that Isolation Forest or PCA/Mahalanobis
catch (KFC!, VAL, MAYNU, ORBS, GREED, SPHERUM, ORBDEG).

## Why DBSCAN underperforms on our data

Most of our validated frauds are **short-lived rug pulls** — median 4
days of on-chain life. DBSCAN assumes that a typical point is surrounded
by other similar points (its `min_samples` parameter defaults to 10
neighbors within `eps`). A 1-day rug with 1 – 50 trades just doesn't have
the neighborhood density to form a cluster, so it gets tossed to "noise."
In principle that sounds perfect for anomaly detection, but it also
means DBSCAN can't tell a *lonely rug* apart from a *lonely legitimate
low-volume token*. Both look like isolated points. Isolation Forest and
PCA-Mahalanobis use more gradient information about *how* outlying a
point is, and that's where the recall gap comes from.

## Why we keep DBSCAN anyway

Three independent detectors triangulating the same question is the
core of the "consensus voting" methodology we inherited from the
project proposal. Removing DBSCAN would drop us to two detectors and
weaken the triangulation argument, even if it's the weakest of the
three.

Importantly, the final **continuous suspicion score** we actually use
is a rank-average across Isolation Forest's continuous decision
function and PCA-Mahalanobis distance. DBSCAN's contribution is the
binary `dbscan_flag` used only for the discrete consensus vote count,
which is no longer our headline number. So the underperformance is
surfaced, understood, and does not contaminate the primary metric.

## Why we are not pivoting to other clustering methods

- **K-means** partitions all points into K groups with no outlier
  concept. It would require a separate step (e.g., distance to cluster
  centroid) to manufacture an anomaly score, and the assumption of
  spherical clusters is poor for high-skew crypto volume data.
- **Hierarchical / agglomerative** gives a dendrogram, not an anomaly
  score. Useful for behavioral typology, not our question.
- **Gaussian Mixture Models** assume Gaussian-shaped clusters. Our
  features are heavy-tailed and bimodal; log-transforming helps only
  partially.
- **HDBSCAN** (a DBSCAN variant with variable density) is the most
  plausible upgrade, but given DBSCAN's role is already demoted in
  our scoring, the marginal benefit is small relative to the extra
  complexity a reviewer would have to follow.

## Bottom line for the poster

> We use clustering via DBSCAN as one of three independent anomaly
> detectors, following the project proposal's triangulation design.
> On our validated subset DBSCAN is the most conservative detector —
> high specificity, lowest recall — largely because short-lived rug
> pulls don't have enough trading history to form neighborhoods. We
> do NOT use it as the primary scoring signal; that role belongs to
> the rank-averaged continuous suspicion score built from Isolation
> Forest and PCA-Mahalanobis. Keeping DBSCAN in the ensemble preserves
> methodological triangulation without letting its limitations drive
> the headline numbers.
