#!/usr/bin/env python3
"""Renumber figures: insert new fig2, shift old fig2→fig3, fig3→fig4, … fig8→fig9.

Applies to notebook source cells only (not outputs).
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Ordered replacements (high → low to avoid double-renaming)
# Each tuple: (old_string, new_string)
REPLACEMENTS = [
    # fig8 → fig9
    ("fig8_partial_dependence", "fig9_partial_dependence"),
    ("'FIG_8'",  "'FIG_9'"),
    ("'fig8'",   "'fig9'"),
    ('"fig8"',   '"fig9"'),
    ("fig:fig8", "fig:fig8"),  # no-op placeholder for manuscript
    # fig7 → fig8  (berm_condition in registry, veg_response_by_condition_texture in manuscript)
    ("fig7_berm_condition", "fig8_berm_condition"),
    ("fig7_veg_response_by_condition_texture", "fig8_veg_response_by_condition_texture"),
    ("'FIG_7'",  "'FIG_8'"),
    ("'fig7'",   "'fig8'"),
    ('"fig7"',   '"fig8"'),
    # fig6 → fig7
    ("fig6_vegetation_response", "fig7_vegetation_response"),
    ("'FIG_6'",  "'FIG_7'"),
    ("'fig6'",   "'fig7'"),
    ('"fig6"',   '"fig7"'),
    # fig5 → fig6
    ("fig5_veg_response_by_condition_texture", "fig6_veg_response_by_condition_texture"),
    ("fig5_berm_condition", "fig6_berm_condition"),
    ("'FIG_5'",  "'FIG_6'"),
    ("'fig5'",   "'fig6'"),
    ('"fig5"',   '"fig6"'),
    # fig4 → fig5
    ("fig4_pca_biplot", "fig5_pca_biplot"),
    ("'FIG_4'",  "'FIG_5'"),
    ("'fig4'",   "'fig5'"),
    ('"fig4"',   '"fig5"'),
    # fig3 → fig4
    ("fig3_controlled_predictors", "fig4_controlled_predictors"),
    ("'FIG_3'",  "'FIG_4'"),
    ("'fig3'",   "'fig4'"),
    ('"fig3"',   '"fig4"'),
    # fig2 → fig3
    ("fig2_model_performance_importance", "fig3_model_performance_importance"),
    ("'FIG_2'",  "'FIG_3'"),
    ("'fig2'",   "'fig3'"),
    ('"fig2"',   '"fig3"'),
]

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
        for old, new in REPLACEMENTS:
            if old != new and old in new_text:
                new_text = new_text.replace(old, new)

        if new_text != src_text:
            count = sum(1 for old, new in REPLACEMENTS if old != new and old in src_text)
            total_changes += count
            cell["source"] = new_text.splitlines(keepends=True)
        else:
            cell["source"] = src_text.splitlines(keepends=True)

    if total_changes:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(nb, f, ensure_ascii=False, indent=1)
        print(f"  ✓ {path.name}: {total_changes} replacement(s)")
    else:
        print(f"  – {path.name}: no changes needed")
    return total_changes


def main():
    print("Renumbering figures in notebooks (fig2→fig3, …, fig8→fig9)…\n")
    total = 0
    for nb_path in NOTEBOOKS:
        if not nb_path.exists():
            print(f"  ✗ {nb_path.name}: NOT FOUND")
            continue
        total += update_notebook(nb_path)
    print(f"\nDone. {total} total replacement(s).")


if __name__ == "__main__":
    main()
