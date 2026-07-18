"""Build an AGU poster (session H138) using the CUAHSI biennial poster as a
visual template: 48x36 in, four columns, Montserrat, teal/navy palette.

Content is the 775-berm remote-sensing study; the design system (canvas size,
fonts, colors, column grid, rounded panels) is inherited from
'CUAHSI biennial.pptx'.

Usage:  python scripts/build_agu_poster.py
Output: agu_poster_H138.pptx  (repo root; gitignored)
"""
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor

REPO = Path(__file__).resolve().parents[1]
FIGS = REPO / "draft" / "overleaf" / "Figures"
OUTC = REPO / "figures" / "outcomes"
OUT = REPO / "agu_poster_H138.pptx"

# ── Template design tokens ───────────────────────────────────────────────────
FONT = "Montserrat"
TEAL = RGBColor(0x14, 0x82, 0xA5)   # title / figure headers
NAVY = RGBColor(0x23, 0x50, 0x78)   # section headers
GREEN = RGBColor(0x5F, 0x7A, 0x66)  # takeaway accent
INK = RGBColor(0x22, 0x22, 0x22)    # body
MUTE = RGBColor(0x60, 0x70, 0x7A)   # captions
PANEL = RGBColor(0xF3, 0xF7, 0xF9)  # light panel fill
PANEL_LN = RGBColor(0xD3, 0xE0, 0xE6)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

def IN(v): return Inches(v)

# 48 x 36 canvas, four 11-in columns
COL_X = [0.6, 12.55, 24.5, 36.45]
COL_W = 11.0
PAD = 0.4                      # inner panel padding
CONTENT_TOP = 7.3
CONTENT_BOT = 35.4
GAP = 0.45                     # vertical gap between panels


def text(slide, s, x, y, w, h, size, color, bold=False, align=PP_ALIGN.LEFT,
         italic=False, anchor=MSO_ANCHOR.TOP, line_spacing=1.05):
    tb = slide.shapes.add_textbox(IN(x), IN(y), IN(w), IN(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    lines = s.split("\n")
    for i, ln in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = line_spacing
        r = p.add_run(); r.text = ln
        r.font.name = FONT; r.font.size = Pt(size); r.font.bold = bold
        r.font.italic = italic; r.font.color.rgb = color
    return tb


def bullets(slide, items, x, y, w, h, size, color):
    tb = slide.shapes.add_textbox(IN(x), IN(y), IN(w), IN(h))
    tf = tb.text_frame; tf.word_wrap = True
    for i, it in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.line_spacing = 1.05
        p.space_after = Pt(10)
        r = p.add_run(); r.text = "▪  " + it
        r.font.name = FONT; r.font.size = Pt(size); r.font.color.rgb = color
    return tb


def panel(slide, x, y, w, h):
    sh = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, IN(x), IN(y), IN(w), IN(h))
    sh.fill.solid(); sh.fill.fore_color.rgb = PANEL
    sh.line.color.rgb = PANEL_LN; sh.line.width = Pt(1.5)
    sh.shadow.inherit = False
    try:
        sh.adjustments[0] = 0.03
    except Exception:
        pass
    return sh


class Column:
    """Stacks section panels down one column."""
    def __init__(self, slide, xi):
        self.slide = slide
        self.x = COL_X[xi]
        self.y = CONTENT_TOP

    def section(self, header, header_color=NAVY, body=None, body_size=21,
                image=None, caption=None, takeaway=None, bullets_items=None,
                img_scale=1.0):
        x, w = self.x, COL_W
        inner_x = x + PAD
        inner_w = w - 2 * PAD
        # measure
        cy = PAD                                   # cursor inside panel (rel)
        parts = []
        # header
        parts.append(("header", cy, header))
        cy += 1.15
        if body:
            nlines = max(1, int(len(body) / (inner_w * 4.0)) + body.count("\n") + 1)
            bh = nlines * (body_size / 72.0 * 1.25) + 0.15
            parts.append(("body", cy, (body, body_size, bh)))
            cy += bh + 0.15
        if bullets_items:
            bh = sum(int(len(b) / (inner_w * 4.2)) + 1 for b in bullets_items) * \
                 (body_size / 72.0 * 1.3) + 0.2 * len(bullets_items)
            parts.append(("bullets", cy, (bullets_items, body_size, bh)))
            cy += bh + 0.1
        if image:
            iw, ih = Image.open(image).size
            disp_w = inner_w * img_scale
            disp_h = disp_w * ih / iw
            parts.append(("image", cy, (image, disp_w, disp_h)))
            cy += disp_h + 0.12
        if caption:
            ch = 0.55 + int(len(caption) / (inner_w * 4.6)) * 0.3
            parts.append(("caption", cy, (caption, ch)))
            cy += ch + 0.05
        if takeaway:
            th = 0.6 + int(len(takeaway) / (inner_w * 3.4)) * 0.42
            parts.append(("takeaway", cy, (takeaway, th)))
            cy += th + 0.05
        cy += PAD - 0.15
        total_h = cy

        # draw panel then content
        panel(self.slide, x, self.y, w, total_h)
        base = self.y
        for kind, ry, payload in parts:
            yy = base + ry
            if kind == "header":
                text(self.slide, payload, inner_x, yy, inner_w, 1.0, 34,
                     header_color, bold=True)
            elif kind == "body":
                s, sz, bh = payload
                text(self.slide, s, inner_x, yy, inner_w, bh, sz, INK)
            elif kind == "bullets":
                items, sz, bh = payload
                bullets(self.slide, items, inner_x, yy, inner_w, bh, sz, INK)
            elif kind == "image":
                img, dw, dh = payload
                left = x + (w - dw) / 2
                self.slide.shapes.add_picture(str(img), IN(left), IN(yy),
                                              IN(dw), IN(dh))
            elif kind == "caption":
                s, ch = payload
                text(self.slide, s, inner_x, yy, inner_w, ch, 16, MUTE, italic=True)
            elif kind == "takeaway":
                s, th = payload
                text(self.slide, s, inner_x, yy, inner_w, th, 22, GREEN, bold=True)
        self.y += total_h + GAP
        return total_h


def build():
    prs = Presentation()
    prs.slide_width = IN(48)
    prs.slide_height = IN(36)
    s = prs.slides.add_slide(prs.slide_layouts[6])

    # ── Title band ───────────────────────────────────────────────────────────
    band = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, IN(0), IN(0), IN(48), IN(6.6))
    band.fill.solid(); band.fill.fore_color.rgb = WHITE
    band.line.fill.background(); band.shadow.inherit = False
    rule = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, IN(0), IN(6.5), IN(48), IN(0.12))
    rule.fill.solid(); rule.fill.fore_color.rgb = TEAL
    rule.line.fill.background(); rule.shadow.inherit = False

    text(s, "Structure is not function: satellite greenness reveals the hydrologic "
            "footprint of legacy water-spreader berms",
         1.0, 0.7, 46.0, 2.6, 62, TEAL, bold=True, align=PP_ALIGN.CENTER)
    text(s, "O. V. Crompton¹, A. N. Koop², S. Anderson³, S. Chaulagain³, "
            "D. A. Lapides⁴, M. B. Meles⁵, M. H. Nichols⁴",
         1.0, 4.05, 46.0, 0.9, 30, NAVY, bold=True, align=PP_ALIGN.CENTER)
    text(s, "¹USDA-ARS Hydrology & Remote Sensing Lab  ·  ²ORISE / USDA-ARS SCINet  ·  "
            "³Univ. of Arizona  ·  ⁴USDA-ARS Southwest Watershed Research Center  ·  "
            "⁵USDA-ARS Sustainable Ag. Water Systems      |      AGU H138 — Human Impacts on the Water Cycle",
         1.0, 5.05, 46.0, 0.8, 19, MUTE, align=PP_ALIGN.CENTER)

    # ── Column 1 — motivation & study system ─────────────────────────────────
    c1 = Column(s, 0)
    c1.section(
        "The unmeasured plumbing of drylands",
        body="Beginning in the 1930s, agencies and ranchers built earthworks across "
             "the US Southwest to slow runoff and force infiltration. More than 1,500 "
             "water-spreader berms remain in the Altar Valley alone. These structures "
             "still redirect water — yet their condition and hydrologic effect are "
             "absent from the models we use to represent human influence on the water "
             "cycle. We ask: after 90 years, which berms still work, and what controls "
             "whether they do?",
        body_size=21)
    c1.section(
        "Study system: Altar Valley, Arizona",
        header_color=TEAL,
        image=OUTC / "fig1_study_area.png",
        caption="775 mapped berms across a 247,000-ha semi-arid watershed, colored by "
                "structural condition (intact vs. degraded).")
    c1.section(
        "By the numbers", header_color=TEAL,
        bullets_items=[
            "1,500+ structures built since the 1930s",
            "775 berms analyzed with Sentinel-2 (2016–2024)",
            "6 soil / landscape predictors; 2 outcomes",
        ], body_size=22)

    # ── Column 2 — approach ──────────────────────────────────────────────────
    c2 = Column(s, 1)
    c2.section(
        "Each berm is a measurement",
        header_color=TEAL,
        image=FIGS / "fig2_veg_response.png",
        caption="Vegetation response ΔS = (upslope − downslope) SAVI, normalized by "
                "background, over August–September 2016–2024.",
        takeaway="Satellite greenness turns a landscape of structures into hundreds of "
                 "field experiments.")
    c2.section(
        "Predictors and analysis",
        body="For each berm we assembled soil texture, soil development (B-horizon), "
             "landform, hillslope slope, flow accumulation, and berm length from NRCS "
             "SSURGO and LiDAR. Two binary outcomes — structural condition (intact vs. "
             "degraded) and vegetation response (ΔS > 7%) — were tested against each "
             "predictor with two-sided Fisher / chi-square tests, controlled logistic "
             "regression, and Random Forests (CV-AUC, permutation importance). A "
             "threshold sweep (0–10%) confirmed the results are not an artifact of the "
             "7% cutoff.",
        body_size=21)
    c2.section(
        "Models recover both outcomes",
        header_color=TEAL,
        image=FIGS / "fig5_model_performance_importance.png",
        caption="Random Forest permutation importance for berm condition and "
                "vegetation response (cross-validated).",
        takeaway="The same landscape predictors skillfully rank both outcomes — but "
                 "rank them differently.")

    # ── Column 3 — what controls each outcome ────────────────────────────────
    c3 = Column(s, 2)
    c3.section(
        "What keeps a berm intact",
        header_color=TEAL,
        image=FIGS / "fig6_berm_condition.png",
        caption="Structural condition by predictor (Fisher / χ² with FDR correction).",
        takeaway="Condition is set by berm length, flow accumulation, and soil texture "
                 "— shorter berms, lower flow accumulation, and finer soils stay intact.")
    c3.section(
        "What drives a vegetation response",
        header_color=TEAL,
        image=FIGS / "fig7_vegetation_response.png",
        caption="Vegetation response by predictor.",
        takeaway="Response follows a different recipe — slope and soil texture; steeper "
                 "slopes and coarser (sandy loam) soils give the largest response.")

    # ── Column 4 — key result, conclusions, refs ─────────────────────────────
    c4 = Column(s, 3)
    c4.section(
        "Structure ≠ function",
        header_color=NAVY,
        image=FIGS / "fig8_veg_response_by_condition_texture.png",
        caption="Co-occurrence of condition and vegetation response across berms.",
        takeaway="An intact berm is not a working berm: structural condition and "
                 "vegetation response are statistically independent (φ ≈ −0.02, p = 0.61).")
    c4.section(
        "Landform is a red herring",
        header_color=TEAL,
        image=FIGS / "fig3_controlled_predictors.png",
        takeaway="Apparent landform effects vanish once slope and soil are controlled.")
    c4.section(
        "Conclusions", header_color=NAVY,
        bullets_items=[
            "Legacy earthworks are a widespread, unrepresented human control on dryland hydrology.",
            "Structure and function are decoupled — condition does not predict vegetation response.",
            "Distinct controls govern each outcome, so a single \"berm effect\" is misleading.",
            "Remote sensing makes the human footprint measurable at the scale of the intervention.",
        ], body_size=20)
    c4.section(
        "Acknowledgements & references", header_color=TEAL,
        body="USDA-NRCS CEAP–Grazing Lands (NR213A750023C013). Soil data: USDA-NRCS "
             "SSURGO. LiDAR: Pima County RFCD.  Berm inventory: Nichols et al. (2021), "
             "Catena. Vegetation metric after Crompton et al. (2025).",
        body_size=16)

    prs.save(OUT)
    return prs


def main():
    prs = build()
    print(f"Saved {OUT}  ({len(prs.slides._sldIdLst)} slide, 48x36 in)")


if __name__ == "__main__":
    main()
