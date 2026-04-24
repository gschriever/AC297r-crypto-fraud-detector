"""
Poster generator — AC297r capstone.

55" x 44" landscape (5:4 aspect = 60:48 target).

Layout:
    HEADER (shields + title + authors)
    ROW 1 panels:  The Question   |  Objectives   |  Methods
    ROW 2 panels:  Results + KPI  |  Figures      |  References
    ROW 3 panel:   Conclusions (full-width)
    FOOTER:        Contact

Each panel has a crimson title bar and a soft-blue body you can paste
text into. Figures panel has two embedded charts from ../artifacts/.

To print at 48" x 60":  Design -> Slide Size -> Custom -> 60 wide x 48
tall -> Ensure Fit.
"""

from __future__ import annotations

from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

# ---- Palette ------------------------------------------------------------------
CRIMSON = RGBColor(0xA5, 0x1C, 0x30)
INK = RGBColor(0x2A, 0x2A, 0x2A)
PANEL_BG = RGBColor(0xE8, 0xF1, 0xF8)
PANEL_BORDER = RGBColor(0xB8, 0xCC, 0xDE)
SOFT_GRAY = RGBColor(0xF5, 0xF5, 0xF5)
RULE = RGBColor(0xD8, 0xD8, 0xD8)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
HINT = RGBColor(0x8A, 0x99, 0xA8)

SLIDE_W = Inches(55)
SLIDE_H = Inches(44)
SERIF = "Georgia"
SANS = "Calibri"

ROOT = Path(__file__).resolve().parent
ARTIFACTS = ROOT.parent / "artifacts"
LOGOS = ROOT / "logos"


# ---- Primitives ---------------------------------------------------------------


def set_fill(shape, rgb):
    shape.fill.solid()
    shape.fill.fore_color.rgb = rgb


def set_no_line(shape):
    shape.line.fill.background()


def set_line(shape, rgb, width_pt=1.0):
    shape.line.color.rgb = rgb
    shape.line.width = Pt(width_pt)


def add_drop_shadow(shape, blur_pt=7, dist_pt=3, alpha_pct=28, direction_deg=45):
    """Attach a soft drop shadow to a shape via OXML (python-pptx has no API)."""
    spPr = shape._element.find(qn("p:spPr"))
    if spPr is None:
        return
    for el in spPr.findall(qn("a:effectLst")):
        spPr.remove(el)
    xml = (
        '<a:effectLst xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
        f'<a:outerShdw blurRad="{int(blur_pt * 12700)}" dist="{int(dist_pt * 12700)}" '
        f'dir="{int(direction_deg * 60000)}" algn="tl" rotWithShape="0">'
        f'<a:srgbClr val="000000"><a:alpha val="{int(alpha_pct * 1000)}"/></a:srgbClr>'
        '</a:outerShdw></a:effectLst>'
    )
    spPr.append(etree.fromstring(xml))


def add_text(slide, left, top, width, height, text, *, font=SANS, size=26,
             bold=False, color=INK, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP,
             italic=False, line_spacing=1.2):
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = Inches(0.15)
    tf.margin_right = Inches(0.15)
    tf.margin_top = Inches(0.1)
    tf.margin_bottom = Inches(0.1)
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


TITLE_BAR_H = Inches(1.4)


def add_panel(slide, left, top, width, height, title):
    """Draw panel chrome only — returns (body_x, body_y, body_w, body_h)
    so callers can place content inside the body area."""
    body = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    body.adjustments[0] = 0.05  # more pronounced bevel on the corners
    set_fill(body, PANEL_BG)
    set_line(body, PANEL_BORDER, width_pt=1.25)
    add_drop_shadow(body, blur_pt=10, dist_pt=4, alpha_pct=28)

    # Title bar sits on top — round just the two top corners so it matches
    # the body's rounded top edge cleanly.
    title_bar = slide.shapes.add_shape(
        MSO_SHAPE.ROUND_2_SAME_RECTANGLE, left, top, width, TITLE_BAR_H
    )
    title_bar.adjustments[0] = 0.22
    set_fill(title_bar, CRIMSON)
    set_no_line(title_bar)
    title_bar.shadow.inherit = False
    add_text(slide, left + Inches(0.4), top + Inches(0.25),
             width - Inches(0.8), TITLE_BAR_H - Inches(0.3), title.upper(),
             font=SANS, size=38, bold=True, color=WHITE)

    body_x = left + Inches(0.5)
    body_y = top + TITLE_BAR_H + Inches(0.35)
    body_w = width - Inches(1.0)
    body_h = height - TITLE_BAR_H - Inches(0.6)
    return body_x, body_y, body_w, body_h


def add_placeholder(slide, x, y, w, h, text):
    add_text(slide, x, y, w, h, text,
             font=SANS, size=24, italic=True, color=HINT, line_spacing=1.3)


def add_figure(slide, left, top, width, height, image_path, caption):
    p = Path(image_path)
    placed = False
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
                 "[ insert figure ]", font=SANS, size=22, italic=True,
                 color=HINT, align=PP_ALIGN.CENTER)
    add_text(slide, left, top + height + Inches(0.03), width, Inches(0.8),
             caption, font=SANS, size=20, italic=True, color=INK,
             align=PP_ALIGN.CENTER)


# ---- Build --------------------------------------------------------------------


def build():
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, SLIDE_W, SLIDE_H)
    set_fill(bg, WHITE)
    set_no_line(bg)

    margin = Inches(0.9)

    # --- HEADER -------------------------------------------------------------
    header_h = Inches(4.8)
    shield_w, shield_h = Inches(3.2), Inches(3.6)
    shield_y = Inches(0.6)
    harvard = LOGOS / "harvard-shield.png"
    seas = LOGOS / "H_SEAS_logo_RGB.png"

    def place_shield(x, path):
        if path.exists():
            slide.shapes.add_picture(str(path), x, shield_y, width=shield_w, height=shield_h)
        else:
            sh = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, shield_y, shield_w, shield_h)
            set_fill(sh, SOFT_GRAY)
            set_line(sh, RULE, 0.75)
            sh.shadow.inherit = False
            add_text(slide, x, shield_y + shield_h / 2 - Inches(0.3), shield_w, Inches(0.7),
                     "[ shield ]", font=SANS, size=20, italic=True,
                     color=HINT, align=PP_ALIGN.CENTER)

    place_shield(margin, harvard)
    place_shield(SLIDE_W - margin - shield_w, seas)

    add_text(slide, margin + shield_w + Inches(0.4), Inches(0.6),
             SLIDE_W - 2 * (margin + shield_w + Inches(0.4)), Inches(2.6),
             "Detecting crypto fraud without labels:\n14 of 15 known rug pulls recovered from 4,334 Ethereum tokens.",
             font=SERIF, size=54, bold=True, color=CRIMSON,
             align=PP_ALIGN.CENTER, line_spacing=1.05)
    add_text(slide, margin + shield_w + Inches(0.4), Inches(3.2),
             SLIDE_W - 2 * (margin + shield_w + Inches(0.4)), Inches(0.7),
             "Gillian Schriever  ·  Jiahui (Cecilia) Cai  ·  Zhilin Chen  ·  Jinghan Huang",
             font=SERIF, size=26, color=INK, align=PP_ALIGN.CENTER)
    add_text(slide, margin + shield_w + Inches(0.4), Inches(3.9),
             SLIDE_W - 2 * (margin + shield_w + Inches(0.4)), Inches(0.6),
             "Harvard John A. Paulson School of Engineering and Applied Sciences  —  AC297r Capstone, Spring 2026",
             font=SERIF, size=20, italic=True, color=INK, align=PP_ALIGN.CENTER)

    divider = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, header_h, SLIDE_W, Inches(0.1))
    set_fill(divider, CRIMSON)
    set_no_line(divider)
    divider.shadow.inherit = False

    # --- GRID DIMENSIONS ----------------------------------------------------
    n_cols = 3
    gutter = Inches(0.7)
    content_w = SLIDE_W - 2 * margin - gutter * (n_cols - 1)
    col_w = content_w / n_cols
    col_xs = [margin + i * (col_w + gutter) for i in range(n_cols)]

    row1_top = header_h + Inches(0.6)
    row1_h = Inches(10.0)
    row2_top = row1_top + row1_h + Inches(0.5)
    row2_h = Inches(14.0)
    row3_top = row2_top + row2_h + Inches(0.5)
    row3_h = Inches(8.8)
    footer_top = row3_top + row3_h + Inches(0.3)

    # --- ROW 1 : Question | Objectives | Methods ----------------------------
    bx, by, bw, bh = add_panel(slide, col_xs[0], row1_top, col_w, row1_h, "① The Question")
    add_placeholder(slide, bx, by, bw, bh,
        "[ Paste your 'question and motivation' text here. ]\n\n"
        "  •  Why fraud detection on-chain is hard\n"
        "  •  Why labels don't work in crypto\n"
        "  •  Our two-layer approach in 1–2 sentences")

    bx, by, bw, bh = add_panel(slide, col_xs[1], row1_top, col_w, row1_h, "② Objectives")
    add_placeholder(slide, bx, by, bw, bh,
        "[ Paste your objectives here. ]\n\n"
        "Suggested:\n"
        "  •  Flag suspicious tokens without supervised labels\n"
        "  •  Distinguish fraud from other anomaly types\n"
        "  •  Validate against documented rug-pulls and hacks\n"
        "  •  Deliver an interpretable, reproducible pipeline")

    bx, by, bw, bh = add_panel(slide, col_xs[2], row1_top, col_w, row1_h, "③ Methods")
    add_placeholder(slide, bx, by, bw, bh,
        "[ Paste your methods here. ]\n\n"
        "Suggested:\n"
        "  •  4,334 mid-cap ERC-20 tokens (Dune Analytics)\n"
        "  •  Six features; rank-averaged across three detectors\n"
        "      (Isolation Forest + DBSCAN + PCA/Mahalanobis)\n"
        "  •  Layer-2 logistic regression on n = 144 labels,\n"
        "      evaluated by leave-one-out CV")

    # --- ROW 2 : Results + KPI | Figures | References -----------------------
    # Results panel
    bx, by, bw, bh = add_panel(slide, col_xs[0], row2_top, col_w, row2_h, "④ Results")
    kpi_h = Inches(3.6)
    kpi_box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                     bx, by, bw, kpi_h)
    kpi_box.adjustments[0] = 0.08
    set_fill(kpi_box, WHITE)
    set_line(kpi_box, PANEL_BORDER, width_pt=1.0)
    add_drop_shadow(kpi_box, blur_pt=6, dist_pt=2, alpha_pct=22)
    add_text(slide, bx, by + Inches(0.1), bw, Inches(2.0),
             "14 / 15",
             font=SERIF, size=92, bold=True, color=CRIMSON, align=PP_ALIGN.CENTER)
    add_text(slide, bx, by + Inches(2.15), bw, Inches(1.3),
             "known frauds recovered at the p85 suspicion cutoff.\n"
             "Legacy three-vote consensus recovered 4 of 15.",
             font=SANS, size=20, italic=True, color=INK, align=PP_ALIGN.CENTER,
             line_spacing=1.2)
    add_placeholder(slide, bx, by + kpi_h + Inches(0.3), bw, bh - kpi_h - Inches(0.3),
        "[ Paste any additional results text here. ]\n\n"
        "  •  Layer-2 LOO accuracy: 0.87\n"
        "  •  Specificity on non-fraud: 88%\n"
        "  •  Detected a coordinated rug cluster\n"
        "      (ORBDEG / SPHERUM / ORBS)")

    # Figures panel
    bx, by, bw, bh = add_panel(slide, col_xs[1], row2_top, col_w, row2_h, "⑤ Figures")
    half_h = (bh - Inches(1.4)) / 2   # reserve ~0.7" per caption
    fig1_h = half_h - Inches(0.3)
    add_figure(slide, bx + Inches(0.1), by + Inches(0.1),
               bw - Inches(0.2), fig1_h,
               ARTIFACTS / "baseline_comparison.png",
               "Fig. 1.  Fraud recall across strategies (n = 144).")
    fig2_top = by + fig1_h + Inches(1.1)
    fig2_h = bh - (fig1_h + Inches(1.4))
    add_figure(slide, bx + Inches(0.1), fig2_top,
               bw - Inches(0.2), fig2_h,
               ARTIFACTS / "shap_global_importance.png",
               "Fig. 2.  SHAP importance — Isolation Forest.")

    # References panel
    bx, by, bw, bh = add_panel(slide, col_xs[2], row2_top, col_w, row2_h, "⑥ References")
    add_text(slide, bx, by, bw, bh,
        "[1]  Mazorra, B. et al.\n"
        "       Do Not Rug on Me: Zero-Dimensional Scam\n"
        "       Detection.  arXiv:2201.07220, 2022.\n\n"
        "[2]  Liu, F. T., Ting, K. M., & Zhou, Z.-H.\n"
        "       Isolation Forest.  ICDM, 2008.\n\n"
        "[3]  Ester, M., Kriegel, H.-P., Sander, J., & Xu, X.\n"
        "       A density-based algorithm for discovering\n"
        "       clusters.  KDD, 1996.\n\n"
        "[4]  Lundberg, S. M. & Lee, S.-I.\n"
        "       A unified approach to interpreting model\n"
        "       predictions.  NeurIPS, 2017.\n\n"
        "[ Add additional references here. ]",
        font=SANS, size=20, color=INK, line_spacing=1.25)

    # --- ROW 3 : Conclusions (full width) -----------------------------------
    concl_w = SLIDE_W - 2 * margin
    bx, by, bw, bh = add_panel(slide, margin, row3_top, concl_w, row3_h, "⑦ Conclusions")
    add_placeholder(slide, bx, by, bw, bh,
        "[ Paste your conclusions / 'so what' here. ]\n\n"
        "Suggested talking points:\n"
        "  •  Continuous ranking beats discrete voting (14 / 15 vs. 4 / 15 fraud recall) — the headline result of the project.\n"
        "  •  Two layers separate 'anomaly' from 'fraud.' Layer-2 specificity of 88% means blue-chip false alarms\n"
        "      (WLFI, DEGEN, 3Crv, MIM) are correctly dismissed while known rugs (WFT, PLASMA, ORBDEG cluster) score > 0.8.\n"
        "  •  Honest limitations — small-volume honeypots (HYPER, KUBO) still slip through; catching them needs\n"
        "      graph-level signals (deployer history, liquidity-pool removal) beyond on-chain volume features.\n"
        "  •  Next step — grow the labeled registry further and add a Layer-3 graph feature set.")

    # --- FOOTER (contact, minimal) -----------------------------------------
    footer_h = SLIDE_H - footer_top - Inches(0.3)
    add_text(slide, margin, footer_top, SLIDE_W - 2 * margin, footer_h,
             "Code:  github.com/gschriever/AC297r-crypto-fraud-detector     "
             "Contact:  [ name ]  ·  [ email ]     "
             "Advisor:  [ advisor ]",
             font=SANS, size=20, color=INK, align=PP_ALIGN.CENTER)

    out = ROOT / "AC297r_Poster_Template.pptx"
    prs.save(str(out))
    return out


def main():
    print(f"Saved {build()}")


if __name__ == "__main__":
    main()
