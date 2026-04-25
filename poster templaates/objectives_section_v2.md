# Poster — updated Objectives section (drop into the "② Objectives" panel)

Layout target: middle column of Row 1 in the AC297r poster template,
~17″ wide on the 55×44″ canvas. Replace everything currently inside
the panel body. The crimson "② OBJECTIVES" header bar stays.

Same poster guidelines as before: ≥24 pt body text, plain English,
generous white space, one anchoring visual.

The intent is to land **two big ideas** in this panel:
  1. The high-level "what we built and why" in one sentence.
  2. The fact that the team built **two parallel pipelines**, with this
     poster covering only the unsupervised side — naming the supervised
     side without trying to explain it.

---

## What to put in the panel — text

### Hook line (large, ~34 pt, bold)

> **Build a fraud detector that needs no labeled examples — and
> compare it against one that does.**

### Two-pipeline diagram (see "Visual" below)

### Three concrete goals (~24 pt, numbered)

For the unsupervised side specifically:

1. **Flag** suspicious tokens from raw on-chain activity alone.
2. **Calibrate** how likely each flag is actually fraud — versus a
   hack, a bug, or normal market noise.
3. **Explain** every flag in human-readable terms, so a reviewer
   can trust or push back on any prediction.

### Optional one-line scope footer (~22 pt italic)

> *This poster covers the unsupervised pipeline (above, left). The
> supervised pipeline is presented separately by the team's other
> half.*

---

## Visual — drop in the middle of the panel

### Option A (preferred) — two-pipeline side-by-side

Two equal-width rounded rectangles, one labeled SUPERVISED, one
UNSUPERVISED, sitting next to each other:

```
┌───────────────────────────┐    ┌───────────────────────────┐
│      UNSUPERVISED         │    │       SUPERVISED          │
│      (this poster)        │    │     (parallel team)       │
│                           │    │                           │
│   Finds tokens whose      │    │   Trained on past         │
│   behavior looks unusual  │    │   pump-and-dump examples  │
│   — including patterns    │    │   to recognize the        │
│   we've never seen.       │    │   textbook pattern.       │
└───────────────────────────┘    └───────────────────────────┘
              ↘                  ↙
        Together they cover
        both novel scams and textbook ones.
```

Color choices:
- UNSUPERVISED box: soft-blue fill (matches the rest of the poster
  panels) with a Harvard-crimson border to signal "this is ours."
- SUPERVISED box: soft-gray fill, lighter-gray border, to visually
  defer to the unsupervised side without dismissing it.
- Convergence text below in plain dark gray, ~22 pt italic.

This makes the two-pipeline architecture instantly legible at 6+
feet without the reader needing to read either box.

### Option B — split-funnel flowchart

A single token at the top branches into the two pipelines, then both
re-converge into a single "Fraud verdict" box. More dynamic but more
ink, and arguably harder to read at distance.

```
            ┌────────────┐
            │   Token    │
            └─────┬──────┘
              ┌───┴───┐
              ↓       ↓
       UNSUPERVISED  SUPERVISED
              ↓       ↓
              └───┬───┘
                  ↓
          Fraud verdict + confidence
```

Use Option B only if Option A leaves the panel feeling sparse.

### Option C — minimalist icon row

Three large icons (✦ flag, ⚖ scale, 🔍 magnifier) above the three
numbered goals, no two-pipeline diagram at all. Saves space if the
two-pipeline framing is moved to Methods. Cleanest visually but
loses the "two pipelines" signal that the user wanted included.

---

## How this connects to the rest of the poster

- **Question panel** (column 1) sets up *why anyone should care* about
  crypto scams — the FBI's $5.6 B figure and the ACCUMULATE → PUMP →
  DUMP playbook.
- **Objectives panel** (column 2 — this one) translates the question
  into *what we set out to build* and signals that there are two
  parallel approaches.
- **Methods panel** (column 3) goes one level deeper into how the
  unsupervised pipeline actually works.
- **Results / Figures / References** (Row 2) and **Conclusions** (Row
  3) stay as they are.

The hook line in this panel is deliberately worded to mirror the
"What we set out to do" framing from the original mid-semester deck
(Project Goals & Success Criteria slide). The three numbered goals
are the same three success criteria, translated out of jargon:

| Mid-semester success criterion                          | Plain-English version on this poster |
|---|---|
| G1 — Scalable feature pipeline for 5,000 tokens          | "Flag suspicious tokens from raw on-chain activity" |
| G2 — Per-token fraud probability with 90% CI             | "Calibrate how likely each flag is actually fraud" |
| G3 — Blockchain features must beat price/volume by ≥5%   | "Explain every flag in human-readable terms"        |

(The third goal moved from "outperform price/volume" to "explainability"
because explainability is what the project actually delivered for the
unsupervised side via SHAP — and explainability is something a non-
technical reader can immediately see the value of.)

## Spec for the layout

| Element                       | Approx. font (in 55×44 file) | Final at 60×48 print |
|---|---|---|
| Hook line                     | 34 pt bold                   | ~37 pt               |
| Two-pipeline box label        | 26 pt bold                   | ~28 pt               |
| Two-pipeline box body         | 22 pt                        | ~24 pt               |
| "Together they cover…" caption| 22 pt italic                 | ~24 pt               |
| Numbered goals (1, 2, 3)      | 26 pt bold + 22 pt body      | ~28 / 24 pt          |
| Optional scope footer         | 22 pt italic                 | ~24 pt               |

Print scaling factor 60/55 = 1.09. All body text comfortably above
the 24 pt minimum after scaling.
