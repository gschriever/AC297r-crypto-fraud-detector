# Session notes — 2026-04-24

Plain-English summary of what changed in the most recent round of
work, written for a reader who hasn't been following the day-to-day.

---

## Tested the professor's Bitcoin-normalization suggestion

- We ran an experiment based on the idea that a lot of small-cap
  crypto activity is really just following Bitcoin's daily ups and
  downs — so if we strip Bitcoin out of each token's signal, we should
  see the truly *token-specific* behavior more clearly.
- We updated our Dune SQL query to pull Bitcoin (WBTC) trading activity
  alongside each token's activity, and computed four new "Bitcoin-
  adjusted" signals per token. The results loaded into our pipeline
  cleanly.
- **But the experiment hurt our fraud-detection numbers** — adding
  the Bitcoin-adjusted signals directly into the detector made it miss
  more known rug pulls (14 out of 15 caught, down to 11 out of 15).

## Why it hurt (the interesting part)

- Most of the fraud tokens we've validated are **short-lived rug pulls
  that only existed for 1 to 4 days**. That's simply not enough time
  to measure whether a token moves *with* Bitcoin or independently of
  it — the Bitcoin-adjusted signals are mathematically undefined or
  extremely noisy on such brief windows.
- When we filled those missing values with cohort averages, the
  short-lived rugs ended up looking "average" in the new dimensions,
  pulling their overall suspicion score *down*. The Bitcoin signals
  were adding noise to exactly the class of tokens we care about
  most.

## What we kept

- Rolled back Bitcoin integration from the fraud detector itself.
- Kept the Bitcoin data and re-purposed it as an **annotation**: for
  each flagged token, the pipeline now writes a "Bitcoin contamination
  score" (0 to 1) that tells a reviewer how much of the token's
  activity is plausibly Bitcoin-driven.
- Verified the annotation on a known fraud: the honeypot HYPER scored
  0.03, correctly indicating its anomaly is token-specific rather than
  market-driven. Stablecoins and big-volume legitimate tokens score
  0.4 and up, which is also what we'd expect.
- Wrote up the experiment, the diagnosis, and the final design in the
  `README` so the reasoning survives past this conversation.

## Addressed the professor's clustering question

- Wrote a reference note, [`notes_clustering.md`](notes_clustering.md),
  explaining where clustering sits in our pipeline, what the numbers
  actually show, and why we're keeping our current design.
- Headline numbers: on the 15 known-fraud tokens, our clustering
  detector (DBSCAN) catches 27% — the weakest of our three detectors —
  but it flags only 14% of normal tokens by mistake, making it the
  most selective.
- **Our position:** keep DBSCAN in the ensemble for methodological
  triangulation (three independent perspectives), but don't let it
  drive the headline score. The main "suspicion score" we report is
  built from our other two detectors.
- We're not pivoting to a different clustering method (k-means,
  hierarchical, etc.) because their design assumptions don't fit
  an anomaly-detection problem with heavy-tailed crypto volume
  data.

## Drafted the poster introduction

- Wrote [`draft_introduction.md`](draft_introduction.md) — about 175
  words, three short paragraphs, no technical jargon, aimed at a
  general undergraduate reader.
- Names both pipelines (supervised + unsupervised) and notes that this
  poster covers only the unsupervised side.
- Closes on a single crisp question that can double as a pull-quote
  on the poster.

## Files added or changed this session

- [`poster templaates/notes_clustering.md`](notes_clustering.md) — new
- [`poster templaates/draft_introduction.md`](draft_introduction.md) — new
- `pipeline.py`, `README.md`, `dune queries/BTC_Normalized_Features_EXPORT.csv`
  — already committed earlier in the session

Note: the poster PowerPoint and its Python generator live in the team's
Google Drive folder, not this repo, to keep the source of truth in one
place. Don't commit `.pptx` posters back into `poster templaates/`.

## Deferred, revisit later

- Re-examine Bitcoin normalization once the validated registry contains
  more long-lived tokens (where the Bitcoin signal is actually
  measurable).
- If we get access to the supervised-pipeline teammates' repo, weave
  a sentence or two about their approach into the poster's intro.
