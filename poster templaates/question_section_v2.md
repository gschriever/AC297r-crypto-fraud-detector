# Poster — updated Question section (drop into the "① The Question" panel)

Layout target: the left-most column of Row 1 in the AC297r poster
template, ~17″ wide on the 55×44″ canvas. Replace everything currently
inside the panel body. The crimson "① THE QUESTION" header bar stays.

Follows the professor's poster guidelines:
- ≥24 pt body text
- Plain English, no algorithm names, no statistics jargon
- Clear flow, plenty of white space
- One concrete number to anchor the stakes

---

## What to put in the panel — text

### Hook line (large, ~36 pt, bold)

> **Can we spot a crypto scam — before it walks away with the money?**

### Body paragraph (~26 pt regular)

> In 2023 alone, **$5.6 billion** disappeared in cryptocurrency fraud.
> Small, lightly-traded tokens are the easiest target: anyone can
> launch one, drum up hype, and quietly cash out — leaving ordinary
> buyers with worthless coins.

### Mini diagram (see "Visual" below)

> The classic scam playbook is three steps:
>
>     ACCUMULATE   →   PUMP   →   DUMP

### Closing question (italicized, ~28 pt, bottom of the panel)

> *Using only what's visible on the public blockchain, can we tell a
> fraudulent token from a legitimate one — without any prior labels,
> and before the damage is done?*

---

## Visual — drop in the middle of the panel

### Option A (preferred) — the three-stage P&D flow

Three rounded rectangles connected by arrows, in a single horizontal
row. Same crimson + soft-blue palette as the rest of the poster:

```
┌──────────────┐    →    ┌──────────────┐    →    ┌──────────────┐
│  ACCUMULATE  │         │     PUMP     │         │     DUMP     │
│ buy cheap    │         │ fake volume  │         │ sell to      │
│ tokens       │         │ + hype       │         │ retail buyers│
└──────────────┘         └──────────────┘         └──────────────┘
```

This is borrowed directly from the mid-semester deck (slide 3) so the
shape will be familiar to the professor. Keep the box fill light
(soft-blue or soft-gray) and the arrows in Harvard crimson so they
read at distance.

### Option B (if A is too tall) — a single hero number

A large numeric callout where the diagram would go:

> **$5.6 B**
> lost to crypto fraud in 2023 (FBI Internet Crime Report)

Set "$5.6 B" at ~120 pt in Harvard crimson serif, with the caption
underneath in 22 pt italic gray. Maximum stopping power for a
passer-by, no diagram needed.

### Option C — actual screenshot

A clean candlestick chart showing a textbook pump-and-dump curve
(steep run-up, sharp collapse). Recommend pulling from one of our
validated FRAUD tokens — e.g., GREED or VAL on DEXScreener
(`dexscreener.com/ethereum/<address>`) — and screenshotting the chart
view. Caption: *"GREED — the typical pattern this poster is about."*

---

## Why this version is better than the previous draft

- **Stakes up front.** The $5.6 B number anchors the problem in dollars
  before any methodology talk. Most undergrad readers don't know how
  much crypto fraud costs each year.
- **Specific, not vague.** "Spot a crypto scam" is more concrete than
  "detect suspicious behavior." It also matches the project's actual
  origin (the mid-semester deck titled the project "Detecting
  Pump-and-Dump in Small-Cap Ethereum Tokens").
- **One question, one frame.** The closing italicized line is the
  whole project's research question in one sentence, deliberately
  worded the same way it appears in the Conclusions panel for visual
  recall as the reader walks across the poster.
- **No mention of supervised vs. unsupervised here.** That distinction
  belongs in Methods or Objectives. The Question panel just sets up
  why anyone should care.

## Spec for the layout

| Element             | Approx. font size (in 55×44 file) | Final at 60×48 print |
|---|---|---|
| Hook line           | 36 pt                              | ~39 pt               |
| Body paragraph      | 26 pt                              | ~28 pt               |
| Diagram box label   | 22 pt bold                         | ~24 pt               |
| Diagram box caption | 18 pt                              | ~20 pt               |
| Closing question    | 28 pt italic                       | ~30 pt               |

(Print scaling factor 60/55 = 1.09. The 18 pt diagram captions are
borderline — bump to 20 pt if there's room.)

## Notes for the rest of the poster

- The "two pipelines" framing (supervised + unsupervised) does not
  appear in the Question panel anymore. It belongs in Objectives or
  Methods, where there's room to do it justice in one short sentence:
  *"Our team built two parallel detection systems — one trained on
  past examples (supervised), one that needs no examples at all
  (unsupervised). This poster covers the unsupervised side."*
- The closing question on the Question panel should be repeated
  verbatim in the Conclusions panel to give the reader a sense of
  closure when they finish the poster.
