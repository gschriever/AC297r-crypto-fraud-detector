"""
Poster generator — AC297r capstone.

Builds a 55" x 44" landscape poster (5:4 aspect ratio matching the briefed
48" x 60" target) following the professor's guidelines:

  - Results-driven title.
  - Three-column Question -> Methods -> Results -> SO WHAT flow.
  - Body text >= 24pt, title ~62pt, section headers 42pt (all scale up
    cleanly when the poster is printed at 60" x 48").
  - Single "SO WHAT" crimson banner across the bottom.
  - Two compatible fonts only: Georgia (serif, title), Calibri (sans, body).
  - High whitespace; figures embedded from ../artifacts/.

Output: AC297r_Poster_Template.pptx in this folder.

To print at exactly 48" x 60" (the professor's spec):
  Open in PowerPoint -> Design -> Slide Size -> Custom Slide Size ->
  60" wide x 48" tall -> Ensure Fit.  PowerPoint scales every element
  proportionally.
"""

from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt

# ---- Palette ------------------------------------------------------------------
CRIMSON = RGBColor(0xA5, 0x1C, 0x30)
INK = RGBColor(0x2A, 0x2A, 0x2A)
SOFT = RGBColor(0xF5, 0xF5, 0xF5)
RULE = RGBColor(0xD8, 0xD8, 0xD8)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

# ---- Dimensions (landscape, 5:4 ratio matching 60x48) -------------------------
SLIDE_W = Inches(55)
SLIDE_H = Inches(44)

SERIF = "Georgia"
SANS = "Calibri"

ROOT = Path(__file__).resolve().parent
ARTIFACTS = ROOT.parent / "artifacts"
LOGOS = ROOT / "logos"


# ---- Helpers ------------------------------------------------------------------


def set_fill(shape, rgb):
    shape.fill.solid()
    shape.fill.fore_color.rgb = rgb


def set_no_line(shape):
    shape.line.fill.background()


def set_line(shape, rgb, width_pt=1.0):
    shape.line.color.rgb = rgb
    shape.line.width = Pt(width_pt)


def add_text(slide, left, top, width, height, text, *, font=SANS, size=26,
             bold=False, color=INK, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
             italic=False, line_spacing=1.2):
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = Inches(0.1)
    tf.margin_right = Inches(0.1)
    tf.margin_top = Inches(0.05)
    tf.margin_bottom = Inches(0.05)
    for i, line in enumerate(text.split("\n")):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = line_spacing
        run = p.add_run()
        run.text = line
        run.font.name = font
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.italic = italic
        run.font.color.rgb = color
    return tb


def add_rule(slide, left, top, width, color=CRIMSON):
    shp = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, Inches(0.04))
    set_fill(shp, color)
    set_no_line(shp)
    shp.shadow.inherit = False
    return shp


def add_section_header(slide, left, top, width, label):
    add_text(slide, left, top, width, Inches(0.9), label.upper(),
             font=SANS, size=42, bold=True, color=CRIMSON)
    add_rule(slide, left, top + Inches(1.0), width * 0.35)


def add_figure(slide, left, top, width, height, image_path, caption):
    placed = False
    p = Path(image_path)
    if p.exists():
        try:
            slide.shapes.add_picture(str(p), left, top, width=width, height=height)
            placed = True
        except Exception:
            placed = False
    if not placed:
        frame = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
        set_fill(frame, WHITE)
        set_line(frame, RULE, 1.0)
        frame.shadow.inherit = False
        add_text(slide, left, top + height / 2 - Inches(0.3), width, Inches(0.8),
                 "[ insert figure ]", font=SANS, size=24, italic=True,
                 color=RGBColor(0x99, 0x99, 0x99), align=PP_ALIGN.CENTER)
    add_text(slide, left, top + height + Inches(0.05), width, Inches(1.0),
             caption, font=SANS, size=22, italic=True, color=INK,
             align=PP_ALIGN.CENTER)


# ---- Build --------------------------------------------------------------------


def build():
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    # Background
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_W, SLIDE_H)
    set_fill(bg, WHITE)
    set_no_line(bg)

    margin = Inches(0.9)

    # --- HEADER (shields + title + authors) ---
    header_h = Inches(4.8)
    shield_w = Inches(3.2)
    shield_h = Inches(3.6)
    shield_y = Inches(0.6)

    harvard_png = LOGOS / "harvard-shield.png"
    seas_png = LOGOS / "H_SEAS_logo_RGB.png"

    def place_shield(x, path):
        if path.exists():
            slide.shapes.add_picture(str(path), x, shield_y, width=shield_w, height=shield_h)
        else:
            sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, shield_y, shield_w, shield_h)
            set_fill(sh, SOFT)
            set_line(sh, RULE, 0.75)
            sh.shadow.inherit = False
            add_text(slide, x, shield_y + shield_h / 2 - Inches(0.3), shield_w, Inches(0.7),
                     "[ shield ]", font=SANS, size=20, italic=True,
                     color=RGBColor(0x99, 0x99, 0x99), align=PP_ALIGN.CENTER)

    place_shield(margin, harvard_png)
    place_shield(SLIDE_W - margin - shield_w, seas_png)

    # Title — results-driven, specific number updated for n=144 registry.
    add_text(
        slide,
        margin + shield_w + Inches(0.4),
        Inches(0.6),
        SLIDE_W - 2 * (margin + shield_w + Inches(0.4)),
        Inches(2.6),
        "Detecting crypto fraud without labels:\n14 of 15 known rug pulls recovered from 4,334 Ethereum tokens.",
        font=SERIF,
        size=56,
        bold=True,
        color=CRIMSON,
        align=PP_ALIGN.CENTER,
        line_spacing=1.05,
    )
    add_text(
        slide,
        margin + shield_w + Inches(0.4),
        Inches(3.2),
        SLIDE_W - 2 * (margin + shield_w + Inches(0.4)),
        Inches(0.7),
        "Gillian Schriever  ·  Jiahui (Cecilia) Cai  ·  Zhilin Chen  ·  Jinghan Huang",
        font=SERIF, size=28, color=INK, align=PP_ALIGN.CENTER,
    )
    add_text(
        slide,
        margin + shield_w + Inches(0.4),
        Inches(3.9),
        SLIDE_W - 2 * (margin + shield_w + Inches(0.4)),
        Inches(0.6),
        "Harvard John A. Paulson School of Engineering and Applied Sciences  —  AC297r Capstone, Spring 2026",
        font=SERIF, size=22, italic=True, color=INK, align=PP_ALIGN.CENTER,
    )

    # Crimson divider under header
    add_rule(slide, 0, header_h, SLIDE_W, color=CRIMSON)

    # --- THREE COLUMNS ---
    body_top = header_h + Inches(0.7)
    n_cols = 3
    gutter = Inches(0.9)
    content_w = SLIDE_W - 2 * margin - gutter * (n_cols - 1)
    col_w = content_w / n_cols
    col_xs = [margin + i * (col_w + gutter) for i in range(n_cols)]

    # Column 1 — The Question / Approach
    cx = col_xs[0]
    add_section_header(slide, cx, body_top, col_w, "The question")
    add_text(
        slide, cx, body_top + Inches(1.4), col_w, Inches(3.0),
        "Can we detect crypto fraud without any labeled data?",
        font=SANS, size=30, bold=True, color=INK, line_spacing=1.15,
    )
    add_text(
        slide, cx, body_top + Inches(4.2), col_w, Inches(10.5),
        (
            "Fraud labels in crypto are rare, slow to publish, and biased\n"
            "toward high-profile cases. Supervised classifiers trained on\n"
            "them don't generalize — the attacks evolve faster than the\n"
            "labels.\n\n"
            "We build a two-layer unsupervised pipeline:\n\n"
            "①  Flag tokens whose on-chain trading behavior looks\n"
            "     statistically unusual.\n\n"
            "②  Estimate how likely that unusual behavior is to be\n"
            "     intentional fraud (vs. a hack, bug, or large legitimate\n"
            "     event)."
        ),
        font=SANS, size=24, color=INK, line_spacing=1.25,
    )

    # Column 2 — Methods
    cx = col_xs[1]
    add_section_header(slide, cx, body_top, col_w, "Methods")
    add_text(
        slide, cx, body_top + Inches(1.4), col_w, Inches(13.5),
        (
            "Data.  4,334 mid-cap ERC-20 tokens on Ethereum\n"
            "(Dune Analytics, 365-day window, $1M–$1B annual volume).\n\n"
            "Features (6).  Volume spike ratio, peak daily volume, days\n"
            "traded, max single-trade dominance, and two 24-hour post-\n"
            "launch velocity features.\n\n"
            "Layer 1 — three independent detectors:\n"
            "    •  Isolation Forest (tree-based outlier detection)\n"
            "    •  DBSCAN (density clustering; keep the noise points)\n"
            "    •  PCA + Mahalanobis distance\n\n"
            "Rank-averaged into a single continuous suspicion score\n"
            "in [0, 1], replacing the legacy three-detector yes/no vote.\n\n"
            "Layer 2.  Logistic regression (L2-regularized) fit on\n"
            "n = 144 hand- and web-validated tokens, mapping suspicious-\n"
            "behavior features to P(fraud). Evaluated with leave-one-out\n"
            "cross-validation."
        ),
        font=SANS, size=24, color=INK, line_spacing=1.25,
    )

    # Column 3 — Results
    cx = col_xs[2]
    add_section_header(slide, cx, body_top, col_w, "Results")

    # Headline KPI box
    kpi_box = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, cx, body_top + Inches(1.4), col_w, Inches(3.2)
    )
    kpi_box.adjustments[0] = 0.06
    set_fill(kpi_box, SOFT)
    set_line(kpi_box, RULE, 0.75)
    kpi_box.shadow.inherit = False
    add_text(
        slide, cx, body_top + Inches(1.55), col_w, Inches(1.6),
        "14 / 15",
        font=SERIF, size=96, bold=True, color=CRIMSON, align=PP_ALIGN.CENTER,
    )
    add_text(
        slide, cx, body_top + Inches(3.3), col_w, Inches(1.2),
        "known frauds recovered at the p85 suspicion cutoff.\n"
        "The legacy three-vote consensus recovered 4 of 15.",
        font=SANS, size=22, italic=True, color=INK, align=PP_ALIGN.CENTER,
        line_spacing=1.2,
    )

    # Figure 1 — lift chart
    fig1_y = body_top + Inches(5.0)
    fig_h = Inches(5.8)
    add_figure(
        slide, cx, fig1_y, col_w, fig_h,
        ARTIFACTS / "baseline_comparison.png",
        "Fig. 1.  Fraud recall on the n = 144 validated subset\n"
        "(15 FRAUD, 129 non-fraud). Continuous suspicion\n"
        "score catches 14 of 15 at p85; discrete voting catches 4.",
    )

    # Figure 2 — SHAP
    fig2_y = fig1_y + fig_h + Inches(2.0)
    fig_h2 = Inches(4.8)
    add_figure(
        slide, cx, fig2_y, col_w, fig_h2,
        ARTIFACTS / "shap_global_importance.png",
        "Fig. 2.  SHAP attribution on Isolation Forest.\n"
        "24-hour early velocity outranks the legacy volume-spike feature.",
    )

    # --- SO WHAT banner ---
    sowhat_y = SLIDE_H - Inches(8.0)
    sowhat_h = Inches(4.8)
    banner = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE, margin, sowhat_y, SLIDE_W - 2 * margin, sowhat_h
    )
    banner.adjustments[0] = 0.03
    set_fill(banner, CRIMSON)
    set_no_line(banner)
    banner.shadow.inherit = False

    add_text(
        slide, margin + Inches(0.6), sowhat_y + Inches(0.25),
        SLIDE_W - 2 * margin - Inches(1.2), Inches(1.1),
        "SO WHAT",
        font=SANS, size=32, bold=True, color=WHITE,
    )
    add_text(
        slide, margin + Inches(0.6), sowhat_y + Inches(1.35),
        SLIDE_W - 2 * margin - Inches(1.2), sowhat_h - Inches(1.4),
        (
            "Continuous ranking beats discrete voting.  A rank-averaged suspicion score recovered 14 of 15 known\n"
            "frauds on the validated subset; the legacy \"3 of 3 detectors agree\" rule recovered only 4 of 15.\n\n"
            "Two layers separate 'anomaly' from 'fraud.'  The Layer-2 calibrator achieves 88% specificity —\n"
            "blue-chip tokens (WLFI, DEGEN, MIM, 3Crv) that trigger Layer 1 alarms all score P(fraud) < 0.06,\n"
            "while known rugs (WFT, PLASMA, ORBDEG cluster) score P(fraud) > 0.8. Leave-one-out accuracy 0.87.\n\n"
            "Remaining limitations.  Small-volume honeypots (HYPER, KUBO) still slip through — catching them\n"
            "requires graph-level signals (deployer history, liquidity-pool removal) beyond on-chain volume."
        ),
        font=SANS, size=24, color=WHITE, line_spacing=1.25,
    )

    # Footer — contact + references
    footer_y = sowhat_y + sowhat_h + Inches(0.35)
    footer_h = SLIDE_H - footer_y - Inches(0.3)
    add_text(
        slide, margin, footer_y, SLIDE_W * 0.5 - margin, footer_h,
        (
            "Code:      github.com/gschriever/AC297r-crypto-fraud-detector\n"
            "Contact:   [ name ]  ·  [ email ]\n"
            "Advisor:   [ advisor ]"
        ),
        font=SANS, size=22, color=INK, line_spacing=1.3,
    )
    add_text(
        slide, SLIDE_W * 0.5, footer_y, SLIDE_W * 0.5 - margin, footer_h,
        (
            "[1] Mazorra et al.  Do Not Rug on Me.  arXiv:2201.07220, 2022.\n"
            "[2] Liu, Ting & Zhou.  Isolation Forest.  ICDM 2008.\n"
            "[3] Lundberg & Lee.  SHAP.  NeurIPS 2017."
        ),
        font=SANS, size=22, color=INK, line_spacing=1.3,
    )

    out = ROOT / "AC297r_Poster_Template.pptx"
    prs.save(str(out))
    return out


def main():
    out = build()
    print(f"Saved {out}")
    print(f"Slide size: 55\" x 44\" landscape (5:4 aspect — same as the 48\"x60\" print target)")
    print(f"To print at exactly 48\" x 60\":")
    print(f"  PowerPoint -> Design -> Slide Size -> Custom -> 60\" wide x 48\" tall -> Ensure Fit")


if __name__ == "__main__":
    main()
