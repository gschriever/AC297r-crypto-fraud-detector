"""
Poster template for AC297r — synthesis of the Harvard SEAS 48x60 template
(Harvard-crimson serif title, shield-flanked header, red contact table) and
the Russell Yang poster (numbered 2x2 panel grid, soft-shaded backgrounds,
yellow callout highlight boxes).

Output: AC297r_Poster_Template.pptx in this folder. Open in PowerPoint and
replace the [bracketed placeholders] with real content.
"""

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Inches, Pt, Emu

# ---- Palette (Harvard crimson + Yang soft panels) ----------------------------
CRIMSON = RGBColor(0xA5, 0x1C, 0x30)
DARK_INK = RGBColor(0x1A, 0x1A, 0x1A)
SOFT_GRAY = RGBColor(0xF2, 0xF2, 0xF2)
SOFT_BLUE = RGBColor(0xE8, 0xEF, 0xF7)
SOFT_SAND = RGBColor(0xFA, 0xF3, 0xE0)
CALLOUT_YELLOW = RGBColor(0xFF, 0xF5, 0xB8)
PANEL_BORDER = RGBColor(0xCC, 0xCC, 0xCC)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

# ---- Slide dimensions (landscape 54W x 42H — PowerPoint caps at 56") ---------
SLIDE_W = Inches(54)
SLIDE_H = Inches(42)

SERIF = "Georgia"
SANS = "Calibri"


def set_fill(shape, rgb):
    shape.fill.solid()
    shape.fill.fore_color.rgb = rgb


def set_no_line(shape):
    shape.line.fill.background()


def set_line(shape, rgb, width_pt=1.0):
    shape.line.color.rgb = rgb
    shape.line.width = Pt(width_pt)


def add_text(
    slide,
    left,
    top,
    width,
    height,
    text,
    *,
    font=SANS,
    size=18,
    bold=False,
    color=DARK_INK,
    align=PP_ALIGN.LEFT,
    anchor=MSO_ANCHOR.TOP,
    italic=False,
):
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = Inches(0.1)
    tf.margin_right = Inches(0.1)
    tf.margin_top = Inches(0.05)
    tf.margin_bottom = Inches(0.05)
    lines = text.split("\n")
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        run = p.add_run()
        run.text = line
        run.font.name = font
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.italic = italic
        run.font.color.rgb = color
    return tb


def add_panel(slide, left, top, width, height, fill=SOFT_GRAY):
    rect = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    rect.adjustments[0] = 0.04
    set_fill(rect, fill)
    set_line(rect, PANEL_BORDER, width_pt=0.75)
    rect.shadow.inherit = False
    return rect


def add_numbered_header(slide, left, top, width, number, title):
    add_text(
        slide,
        left + Inches(0.3),
        top + Inches(0.2),
        width - Inches(0.6),
        Inches(1.1),
        f"{number}. {title}",
        font=SANS,
        size=40,
        bold=True,
        color=CRIMSON,
    )


def add_callout(slide, left, top, width, height, title, body):
    box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    box.adjustments[0] = 0.08
    set_fill(box, CALLOUT_YELLOW)
    set_line(box, RGBColor(0xE0, 0xC8, 0x50), width_pt=1.0)
    box.shadow.inherit = False
    add_text(
        slide,
        left + Inches(0.2),
        top + Inches(0.15),
        width - Inches(0.4),
        Inches(0.8),
        title,
        font=SANS,
        size=22,
        bold=True,
        color=CRIMSON,
    )
    add_text(
        slide,
        left + Inches(0.2),
        top + Inches(1.0),
        width - Inches(0.4),
        height - Inches(1.1),
        body,
        font=SANS,
        size=18,
        color=DARK_INK,
    )


def add_placeholder_figure(slide, left, top, width, height, caption):
    frame = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    set_fill(frame, WHITE)
    set_line(frame, PANEL_BORDER, width_pt=1.0)
    frame.shadow.inherit = False
    add_text(
        slide,
        left,
        top + height / 2 - Inches(0.4),
        width,
        Inches(0.8),
        "[ Insert figure ]",
        font=SANS,
        size=20,
        italic=True,
        color=RGBColor(0x99, 0x99, 0x99),
        align=PP_ALIGN.CENTER,
    )
    add_text(
        slide,
        left,
        top + height + Inches(0.05),
        width,
        Inches(0.5),
        caption,
        font=SANS,
        size=14,
        italic=True,
        color=DARK_INK,
        align=PP_ALIGN.CENTER,
    )


# ---- Build -------------------------------------------------------------------


def build():
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank

    # --- Background ---
    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_W, SLIDE_H)
    set_fill(bg, WHITE)
    set_no_line(bg)

    # --- Header strip: crimson band behind title (SEAS-inspired) ---
    header_h = Inches(5.5)
    band = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_W, header_h)
    set_fill(band, WHITE)
    set_no_line(band)

    underline = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, 0, header_h, SLIDE_W, Inches(0.25)
    )
    set_fill(underline, CRIMSON)
    set_no_line(underline)

    # Harvard shield placeholders (left + right)
    for x in (Inches(1.0), Inches(49.5)):
        shield = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, Inches(0.7), Inches(3.5), Inches(4.0))
        set_fill(shield, SOFT_GRAY)
        set_line(shield, PANEL_BORDER, width_pt=0.75)
        shield.shadow.inherit = False
        add_text(
            slide,
            x,
            Inches(0.7) + Inches(1.5),
            Inches(3.5),
            Inches(1.0),
            "[ shield / logo ]",
            font=SANS,
            size=14,
            italic=True,
            color=RGBColor(0x99, 0x99, 0x99),
            align=PP_ALIGN.CENTER,
        )

    # Title
    add_text(
        slide,
        Inches(5.5),
        Inches(0.5),
        Inches(43),
        Inches(2.4),
        "[ Project Title — Unsupervised Crypto Fraud Detection ]",
        font=SERIF,
        size=66,
        bold=True,
        color=CRIMSON,
        align=PP_ALIGN.CENTER,
    )
    # Authors
    add_text(
        slide,
        Inches(5.5),
        Inches(3.1),
        Inches(43),
        Inches(0.9),
        "Gillian Schriever¹, Jiahui (Cecilia) Cai¹, Zhilin Chen¹, Jinghan Huang¹",
        font=SERIF,
        size=26,
        color=DARK_INK,
        align=PP_ALIGN.CENTER,
    )
    # Affiliation
    add_text(
        slide,
        Inches(5.5),
        Inches(3.9),
        Inches(43),
        Inches(0.8),
        "¹ Harvard John A. Paulson School of Engineering and Applied Sciences — AC297r Capstone, Spring 2026",
        font=SERIF,
        size=20,
        italic=True,
        color=DARK_INK,
        align=PP_ALIGN.CENTER,
    )

    # --- Panel grid (2 x 2) ---
    margin = Inches(1.0)
    gutter = Inches(0.6)
    top_y = header_h + Inches(0.6)
    panel_w = (SLIDE_W - 2 * margin - gutter) / 2
    panel_h = Inches(13.0)

    positions = [
        (margin, top_y),
        (margin + panel_w + gutter, top_y),
        (margin, top_y + panel_h + gutter),
        (margin + panel_w + gutter, top_y + panel_h + gutter),
    ]
    fills = [SOFT_GRAY, SOFT_BLUE, SOFT_SAND, SOFT_GRAY]
    titles = [
        "Background",
        "Methodology",
        "Layer 1 — Suspicious-Behavior Detection",
        "Layer 2 — Fraud Calibration & Explainability",
    ]
    bodies = [
        (
            "Traditional fraud detection relies on labeled datasets — rare and\n"
            "quickly outdated in crypto. We instead build a two-layer\n"
            "unsupervised system:\n\n"
            "   •  Layer 1 flags suspicious behavior\n"
            "   •  Layer 2 estimates P(fraud | suspicious)\n\n"
            "Dataset: 4,334 mid-cap ERC-20 tokens on Ethereum (Dune Analytics,\n"
            "365-day window, $1M–$1B annualized volume).\n\n"
            "[ Why it matters: 1–2 sentences in plain English for the reader\n"
            "who has 5 seconds at your poster. ]"
        ),
        (
            "Features (6): volume_spike_ratio, max_daily_volume, days_traded,\n"
            "max_trade_dominance, early_velocity_ratio, early_trade_dominance.\n\n"
            "Three independent anomaly detectors:\n"
            "   1. Isolation Forest (sparse outliers)\n"
            "   2. DBSCAN (density-based noise points)\n"
            "   3. PCA + Mahalanobis distance (multivariate extremes)\n\n"
            "Rank-averaged to produce a continuous suspicion_score ∈ [0, 1].\n"
            "Layer 2: logistic regression on n=14 hand-validated tokens (LOO-CV)\n"
            "mapping suspicious-behavior features → P(fraud)."
        ),
        (
            "[ Headline finding in plain English. ]\n\n"
            "Continuous suspicion score at p90 cutoff:\n"
            "   •  Flags 10% of tokens\n"
            "   •  Catches 100% of validated fraud (6/6)\n\n"
            "Discrete 3-vote consensus (legacy approach):\n"
            "   •  Flags 2.3% of tokens\n"
            "   •  Catches 17% of validated fraud (1/6)\n\n"
            "[ Figure placeholder below: PCA anomaly map + baseline lift chart. ]"
        ),
        (
            "SHAP feature-importance on Isolation Forest identifies\n"
            "early_velocity_ratio (first-24h volume/total) as the #1 driver of\n"
            "suspicion — validating the 'Do Not Rug on Me' (Mazorra et al.)\n"
            "temporal hypothesis.\n\n"
            "Calibration separates catastrophic non-fraud (SLP / 3Crv / MIM,\n"
            "P(fraud) < 0.15) from rug-like tokens (WFT / PLASMA / GREED,\n"
            "P(fraud) > 0.6). LOO accuracy modest at n=14 — we report this\n"
            "honestly and note what additional labels would buy.\n\n"
            "[ Figure placeholder below: SHAP global importance + calibration report. ]"
        ),
    ]

    for (x, y), fill, num, title, body in zip(
        positions, fills, [1, 2, 3, 4], titles, bodies
    ):
        add_panel(slide, x, y, panel_w, panel_h, fill=fill)
        add_numbered_header(slide, x, y, panel_w, num, title)
        add_text(
            slide,
            x + Inches(0.5),
            y + Inches(1.4),
            panel_w - Inches(1.0),
            Inches(7.5),
            body,
            font=SANS,
            size=18,
            color=DARK_INK,
        )

    # Figure placeholders inside the two Results panels
    fig_w = (panel_w - Inches(1.5)) / 2
    fig_h = Inches(4.5)
    for (x, y), caption_left, caption_right in [
        (
            positions[2],
            "Fig 3a. PCA anomaly map (consensus votes)",
            "Fig 3b. Fraud-recall lift over baselines",
        ),
        (
            positions[3],
            "Fig 4a. SHAP global importance",
            "Fig 4b. LOO calibration on validated subset",
        ),
    ]:
        fx1 = x + Inches(0.5)
        fx2 = x + Inches(0.5) + fig_w + Inches(0.5)
        fy = y + Inches(7.5)
        add_placeholder_figure(slide, fx1, fy, fig_w, fig_h, caption_left)
        add_placeholder_figure(slide, fx2, fy, fig_w, fig_h, caption_right)

    # Callout box inside Methodology panel (Yang-style)
    mx, my = positions[1]
    add_callout(
        slide,
        mx + panel_w - Inches(8.0),
        my + Inches(7.8),
        Inches(7.5),
        Inches(4.5),
        "Key design decision",
        (
            "Move from discrete consensus voting\n"
            "to a continuous rank-averaged score.\n\n"
            "Rationale: the old yes/no voting\n"
            "dropped validated fraud tokens that\n"
            "any single detector happened to miss."
        ),
    )

    # --- Summary strip ---
    strip_y = top_y + 2 * panel_h + 2 * gutter
    strip_h = Inches(3.8)
    add_panel(slide, margin, strip_y, SLIDE_W - 2 * margin, strip_h, fill=SOFT_GRAY)
    add_text(
        slide,
        margin + Inches(0.4),
        strip_y + Inches(0.2),
        SLIDE_W - 2 * margin - Inches(0.8),
        Inches(1.1),
        "5. Summary & Recommendation",
        font=SANS,
        size=40,
        bold=True,
        color=CRIMSON,
    )
    add_text(
        slide,
        margin + Inches(0.5),
        strip_y + Inches(1.4),
        SLIDE_W - 2 * margin - Inches(1.0),
        strip_h - Inches(1.5),
        (
            "[ One-sentence plain-English headline, large, bold. Replace this. ]\n\n"
            "   •  A continuous suspicion score materially outperforms the legacy consensus-vote threshold for fraud recall.\n"
            "   •  The Layer-2 calibrator reliably identifies what is NOT fraud (large legitimate events); separating fraud\n"
            "       from hacks/bugs within the high-suspicion region requires evidence beyond on-chain volume features.\n"
            "   •  Limitations: validation set n=14; token-symbol collisions handled via lowercase dedup; 37% of tokens\n"
            "       have imputed 24-hour features. All limitations disclosed in the accompanying report."
        ),
        font=SANS,
        size=20,
        color=DARK_INK,
    )

    # --- Footer: contact table (SEAS-style) + references ---
    footer_y = strip_y + strip_h + Inches(0.25)
    footer_h = SLIDE_H - footer_y - Inches(0.4)
    # References block (left ~2/3)
    ref_w = Inches(34)
    add_text(
        slide,
        margin,
        footer_y,
        ref_w,
        Inches(0.6),
        "References & Acknowledgments",
        font=SANS,
        size=20,
        bold=True,
        color=CRIMSON,
    )
    add_text(
        slide,
        margin,
        footer_y + Inches(0.7),
        ref_w,
        footer_h - Inches(0.8),
        (
            "1. Mazorra, B. et al. Do Not Rug on Me: Zero-Dimensional Scam Detection. arXiv:2201.07220, 2022.\n"
            "2. Liu, F. T., Ting, K. M., & Zhou, Z.-H. Isolation Forest. ICDM 2008.\n"
            "3. Ester, M. et al. A Density-Based Algorithm for Discovering Clusters. KDD 1996.\n"
            "4. Lundberg, S. M. & Lee, S.-I. A Unified Approach to Interpreting Model Predictions. NeurIPS 2017.\n\n"
            "Data: Dune Analytics (dex.trades, Ethereum, 365-day window). Code: [ github link ]"
        ),
        font=SANS,
        size=14,
        color=DARK_INK,
    )

    # Contact table (right ~1/3, SEAS-crimson style)
    table_x = margin + ref_w + Inches(0.6)
    table_w = SLIDE_W - table_x - margin
    cell_w = table_w / 3
    headers = ["CONTACT", "MORE INFO", "THANK YOU"]
    body_rows = [
        "[ name ]\n[ email ]\n[ website ]",
        "[ github / paper link ]\n[ QR code placeholder ]",
        "[ advisor ]\n[ team / partners ]",
    ]
    for i, (h, b) in enumerate(zip(headers, body_rows)):
        cx = table_x + i * cell_w
        hdr = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, cx, footer_y, cell_w, Inches(0.9))
        set_fill(hdr, CRIMSON)
        set_line(hdr, WHITE, width_pt=2.0)
        hdr.shadow.inherit = False
        add_text(
            slide,
            cx,
            footer_y + Inches(0.15),
            cell_w,
            Inches(0.7),
            h,
            font=SANS,
            size=22,
            bold=True,
            color=WHITE,
            align=PP_ALIGN.CENTER,
        )
        cell = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, cx, footer_y + Inches(0.9), cell_w, footer_h - Inches(0.9)
        )
        set_fill(cell, WHITE)
        set_line(cell, CRIMSON, width_pt=1.5)
        cell.shadow.inherit = False
        add_text(
            slide,
            cx + Inches(0.15),
            footer_y + Inches(1.0),
            cell_w - Inches(0.3),
            footer_h - Inches(1.0),
            b,
            font=SANS,
            size=14,
            color=DARK_INK,
            align=PP_ALIGN.CENTER,
        )

    out = Path(__file__).resolve().parent / "AC297r_Poster_Template.pptx"
    prs.save(str(out))
    print(f"Saved {out}")
    print(f"Slide size: {Emu(prs.slide_width).inches:.0f} x {Emu(prs.slide_height).inches:.0f} inches (landscape)")


if __name__ == "__main__":
    build()
