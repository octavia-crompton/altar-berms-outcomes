#!/usr/bin/env python3
"""Renumber FIG entries in figure_report_outcomes.tex: shift fig2→fig3, …, fig8→fig9.
Add new FIG_2 entry for fig2_veg_response.pdf.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEX = ROOT / "latex" / "figure_report_outcomes.tex"

# Ordered replacements (high → low to avoid double-renaming)
MARKER_MAP = [
    ("FIG_8_START", "FIG_9_START"), ("FIG_8_END", "FIG_9_END"),
    ("FIG_7_START", "FIG_8_START"), ("FIG_7_END", "FIG_8_END"),
    ("FIG_6_START", "FIG_7_START"), ("FIG_6_END", "FIG_7_END"),
    ("FIG_5_START", "FIG_6_START"), ("FIG_5_END", "FIG_6_END"),
    ("FIG_4_START", "FIG_5_START"), ("FIG_4_END", "FIG_5_END"),
    ("FIG_3_START", "FIG_4_START"), ("FIG_3_END", "FIG_4_END"),
    ("FIG_2_START", "FIG_3_START"), ("FIG_2_END", "FIG_3_END"),
]

# Label replacements inside \figentry{figN}{...}
LABEL_MAP = [
    ("{fig8}", "{fig9}"),
    ("{fig7}", "{fig8}"),
    ("{fig6}", "{fig7}"),
    ("{fig5}", "{fig6}"),
    ("{fig4}", "{fig5}"),
    ("{fig3}", "{fig4}"),
    ("{fig2}", "{fig3}"),
]

# Filename replacements
FILE_MAP = [
    ("fig8_partial_dependence.png",               "fig9_partial_dependence.png"),
    ("fig7_berm_condition.png",                    "fig8_berm_condition.png"),
    ("fig6_vegetation_response.png",               "fig7_vegetation_response.png"),
    ("fig5_veg_response_by_condition_texture.png",  "fig6_veg_response_by_condition_texture.png"),
    ("fig4_pca_biplot.png",                         "fig5_pca_biplot.png"),
    ("fig3_controlled_predictors.png",              "fig4_controlled_predictors.png"),
    ("fig2_model_performance_importance.png",        "fig3_model_performance_importance.png"),
]

# Also update the comment headers  "── Fig N ──"
COMMENT_MAP = [
    ("Fig 8", "Fig 9"),
    ("Fig 7", "Fig 8"),
    ("Fig 6", "Fig 7"),
    ("Fig 5", "Fig 6"),
    ("Fig 4", "Fig 5"),
    ("Fig 3", "Fig 4"),
    ("Fig 2", "Fig 3"),
]

NEW_FIG2_BLOCK = """\
% ── Fig 2 ────────────────────────────────────────────────────
%% FIG_2_START
\\figentry%
  {fig2}%
  {fig2_veg_response.pdf}%
  {2026-04-08}%
  {Vegetation response metric illustration for an example berm. Panel~A: upslope, downslope, and background area delineation. Panel~B: SAVI values in these three areas. Panel~C: monthly climatology of SAVI showing the upslope--downslope contrast used to compute the percent-difference metric $\\Delta S$.}%
  {Panel A shows the spatial delineation of upslope, downslope, and background areas around an example berm. Panels B and C illustrate the SAVI time series and climatology that underpin the $\\Delta S$ vegetation response metric.}
%% FIG_2_END

"""


def main():
    text = TEX.read_text(encoding="utf-8")

    for old, new in MARKER_MAP:
        text = text.replace(old, new)
    for old, new in LABEL_MAP:
        text = text.replace(old, new)
    for old, new in FILE_MAP:
        text = text.replace(old, new)
    for old, new in COMMENT_MAP:
        text = text.replace(old, new)

    # Insert new FIG_2 block after FIG_1_END
    anchor = "%% FIG_1_END"
    idx = text.find(anchor)
    if idx >= 0:
        insert_pos = idx + len(anchor)
        # Skip to end of line
        nl = text.find("\n", insert_pos)
        if nl >= 0:
            insert_pos = nl + 1
        text = text[:insert_pos] + "\n" + NEW_FIG2_BLOCK + text[insert_pos:]
        print("  Inserted new FIG_2 block after FIG_1_END")
    else:
        print("  WARNING: FIG_1_END not found; could not insert FIG_2 block")

    TEX.write_text(text, encoding="utf-8")
    print("  ✓ figure_report_outcomes.tex updated")


if __name__ == "__main__":
    main()
