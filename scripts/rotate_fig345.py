#!/usr/bin/env python3
"""Rotate fig3→fig5, fig4→fig3, fig5→fig4 in notebooks.
Uses temp placeholder to avoid double-replacement.
Also fixes FIG_ID markers (double-quoted) that were missed by the earlier renumbering.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 3-way rotation via temp: fig3→TEMP, fig4→fig3, fig5→fig4, TEMP→fig5
# Each tuple: (old, new)
PHASE1 = [  # fig3 → placeholder
    ("fig3_model_performance_importance", "__TMPFIG__model_performance_importance"),
    ('"FIG_2"',   '"__TMPFIG_ID__"'),    # notebook 2: RF FIG marker (was missed by prev rename)
    ('"fig3"',    '"__TMPFIG_LBL__"'),
    ("'fig3'",    "'__TMPFIG_LBL__'"),
]
PHASE2 = [  # fig4 → fig3
    ("fig4_controlled_predictors", "fig3_controlled_predictors"),
    ('"FIG_4"',   '"FIG_3"'),
    ("'FIG_4'",   "'FIG_3'"),
    ('"fig4"',    '"fig3"'),
    ("'fig4'",    "'fig3'"),
]
PHASE3 = [  # fig5 → fig4
    ("fig5_pca_biplot", "fig4_pca_biplot"),
    ('"FIG_5"',   '"FIG_4"'),
    ("'FIG_5'",   "'FIG_4'"),
    ('"fig5"',    '"fig4"'),
    ("'fig5'",    "'fig4'"),
]
PHASE4 = [  # placeholder → fig5
    ("__TMPFIG__model_performance_importance", "fig5_model_performance_importance"),
    ('"__TMPFIG_ID__"',   '"FIG_5"'),
    ('"__TMPFIG_LBL__"',  '"fig5"'),
    ("'__TMPFIG_LBL__'",  "'fig5'"),
]

ALL_PHASES = PHASE1 + PHASE2 + PHASE3 + PHASE4

NOTEBOOKS = [
    ROOT / "notebooks" / "2 analysis - condition vegetation.ipynb",
    ROOT / "notebooks" / "4 analysis - controlled predictors.ipynb",
]


def update_notebook(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        nb = json.load(f)

    total_changes = 0
    for cell in nb["cells"]:
        raw_src = cell.get("source", [])
        if isinstance(raw_src, str):
            src_text = raw_src
        else:
            src_text = "".join(raw_src)

        new_text = src_text
        for old, new in ALL_PHASES:
            if old in new_text:
                new_text = new_text.replace(old, new)

        if new_text != src_text:
            total_changes += 1
            cell["source"] = new_text.splitlines(keepends=True)
        else:
            cell["source"] = src_text.splitlines(keepends=True)

    if total_changes:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(nb, f, ensure_ascii=False, indent=1)
        print(f"  ✓ {path.name}: {total_changes} cell(s) changed")
    else:
        print(f"  – {path.name}: no changes needed")
    return total_changes


def main():
    print("Rotating figures: fig3→fig5, fig4→fig3, fig5→fig4\n")
    total = 0
    for nb_path in NOTEBOOKS:
        if not nb_path.exists():
            print(f"  ✗ {nb_path.name}: NOT FOUND")
            continue
        total += update_notebook(nb_path)
    print(f"\nDone. {total} cell(s) updated.")


if __name__ == "__main__":
    main()
