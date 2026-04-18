#!/usr/bin/env python3
"""Renumber fig entries in figure_registry_concise.txt: fig2→fig3, …, fig8→fig9.
Also update filenames in 'File :' lines.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REG = ROOT / "figures" / "outcomes" / "figure_registry_concise.txt"

# Ordered high→low to avoid double-replacement
REPLACEMENTS = [
    # Headers
    ("### fig8 ###", "### fig9 ###"), ("### end fig8 ###", "### end fig9 ###"),
    ("### fig7 ###", "### fig8 ###"), ("### end fig7 ###", "### end fig8 ###"),
    ("### fig6 ###", "### fig7 ###"), ("### end fig6 ###", "### end fig7 ###"),
    ("### fig5 ###", "### fig6 ###"), ("### end fig5 ###", "### end fig6 ###"),
    ("### fig4 ###", "### fig5 ###"), ("### end fig4 ###", "### end fig5 ###"),
    ("### fig3 ###", "### fig4 ###"), ("### end fig3 ###", "### end fig4 ###"),
    ("### fig2 ###", "### fig3 ###"), ("### end fig2 ###", "### end fig3 ###"),
    # Filenames in 'File :' lines
    ("fig8_partial_dependence.png",               "fig9_partial_dependence.png"),
    ("fig7_berm_condition.png",                    "fig8_berm_condition.png"),
    ("fig6_vegetation_response.png",               "fig7_vegetation_response.png"),
    ("fig5_veg_response_by_condition_texture.png",  "fig6_veg_response_by_condition_texture.png"),
    ("fig4_pca_biplot.png",                         "fig5_pca_biplot.png"),
    ("fig3_controlled_predictors.png",              "fig4_controlled_predictors.png"),
    ("fig2_model_performance_importance.png",        "fig3_model_performance_importance.png"),
]

NEW_FIG2_BLOCK = """\
### fig2 ###
File    : fig2_veg_response.pdf
Updated : 2026-04-08
────────────────────────────────────────────────────────────────────────
Stats   : Vegetation response metric illustration for an example berm.
          Panel A: upslope, downslope, and background area delineation.
          Panel B: SAVI values in these three areas.
          Panel C: monthly climatology of SAVI showing the upslope–downslope contrast.
────────────────────────────────────────────────────────────────────────
Concise : Panels show the spatial delineation, SAVI time series, and
          climatology that underpin the ΔS vegetation response metric.
### end fig2 ###

"""


def main():
    text = REG.read_text(encoding="utf-8")
    for old, new in REPLACEMENTS:
        text = text.replace(old, new)

    # Insert new fig2 block at the top of the file
    text = NEW_FIG2_BLOCK + text
    REG.write_text(text, encoding="utf-8")
    print("  ✓ figure_registry_concise.txt updated")


if __name__ == "__main__":
    main()
