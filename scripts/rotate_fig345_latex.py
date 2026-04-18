#!/usr/bin/env python3
"""Rotate fig3→fig5, fig4→fig3, fig5→fig4 in LaTeX report and registry.
Uses temp placeholders for the 3-way swap.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TEX = ROOT / "latex" / "figure_report_outcomes.tex"
REG = ROOT / "figures" / "outcomes" / "figure_registry_concise.txt"

# Phase 1: fig3 → TEMP
P1 = [
    ("FIG_3_START", "TMPFIG_START"), ("FIG_3_END", "TMPFIG_END"),
    ("{fig3}", "{figTMP}"),
    ("fig3_model_performance_importance", "TMPFIG_model_performance_importance"),
    ("### fig3 ###", "### figTMP ###"), ("### end fig3 ###", "### end figTMP ###"),
    ("Fig 3", "Fig TMP"),  # comment headers
]
# Phase 2: fig4 → fig3
P2 = [
    ("FIG_4_START", "FIG_3_START"), ("FIG_4_END", "FIG_3_END"),
    ("{fig4}", "{fig3}"),
    ("fig4_controlled_predictors", "fig3_controlled_predictors"),
    ("### fig4 ###", "### fig3 ###"), ("### end fig4 ###", "### end fig3 ###"),
    ("Fig 4", "Fig 3"),
    ("fig4_pca_biplot", "fig3_pca_biplot"),  # registry filename if present
]
# Phase 3: fig5 → fig4
P3 = [
    ("FIG_5_START", "FIG_4_START"), ("FIG_5_END", "FIG_4_END"),
    ("{fig5}", "{fig4}"),
    ("fig5_pca_biplot", "fig4_pca_biplot"),
    ("fig5_model_performance_importance", "fig4_model_performance_importance"),
    ("### fig5 ###", "### fig4 ###"), ("### end fig5 ###", "### end fig4 ###"),
    ("Fig 5", "Fig 4"),
]
# Phase 4: TEMP → fig5
P4 = [
    ("TMPFIG_START", "FIG_5_START"), ("TMPFIG_END", "FIG_5_END"),
    ("{figTMP}", "{fig5}"),
    ("TMPFIG_model_performance_importance", "fig5_model_performance_importance"),
    ("### figTMP ###", "### fig5 ###"), ("### end figTMP ###", "### end fig5 ###"),
    ("Fig TMP", "Fig 5"),
    ("fig3_pca_biplot", "fig4_pca_biplot"),  # fix any intermediate collision
]

ALL = P1 + P2 + P3 + P4


def process_file(path: Path):
    text = path.read_text(encoding="utf-8")
    for old, new in ALL:
        text = text.replace(old, new)
    path.write_text(text, encoding="utf-8")
    print(f"  ✓ {path.relative_to(ROOT)}")


def main():
    print("Rotating fig3/4/5 in LaTeX report and registry:\n")
    for f in [TEX, REG]:
        if f.exists():
            process_file(f)
        else:
            print(f"  ✗ {f.relative_to(ROOT)}: not found")


if __name__ == "__main__":
    main()
