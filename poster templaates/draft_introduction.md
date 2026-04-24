# Poster introduction — draft

Audience: general undergraduate reader, no crypto or ML background.
Goal: state why we care, name the problem, and set up the question —
all in about 120 words. Mention both pipelines.

---

## The Question

*(Header on the poster, for the "① The Question" panel.)*

## Why we care

Every year, tens of billions of dollars flow through cryptocurrency
tokens that no longer exist six months later. Some collapse because
of bugs or outside attacks — accidents. Others are deliberate scams:
developers who launch a token, build excitement, take buyers' money,
and disappear. For an ordinary person trying to tell the difference,
the evidence usually arrives far too late.

## What we're trying to do

The standard way to teach a computer to detect fraud is to train it
on past examples that humans have already labeled. That approach is
a poor fit for crypto: confirmed labels are rare, they often surface
years after the fact, and the scams keep evolving. For our capstone
we built **two parallel systems** that attack the same problem from
opposite directions — a supervised pipeline that learns from the
small amount of labeled data available, and an unsupervised pipeline
(the focus of this poster) that flags suspicious token behavior
without relying on any labels at all.

## The underlying question

**Using only the trading activity that anyone can see on the public
blockchain, can we reliably tell a fraudulent token from a legitimate
one — without any labels, and without knowing in advance what the
next scam will look like?**

---

## Notes for the poster

- The "Why we care" paragraph can stand alone as the top of the
  Question panel. The "What we're trying to do" paragraph belongs
  under Objectives (or in Methods if space is tight).
- The bold question at the bottom is the one-sentence hook. It
  should appear prominently — either as a pull-quote under the
  title or as the closing line of the Question panel.
- Jargon check: "on the public blockchain" is the only slightly
  technical phrase and most undergrads know it; no model names,
  no algorithm names, no statistics terms.
- Both pipelines are named but only the unsupervised one is
  promised any further detail on the poster, consistent with the
  scope note.
