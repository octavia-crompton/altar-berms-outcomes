#!/usr/bin/env python3
"""Fix FIG_ID markers in notebook 2 that were missed by the earlier
   renumbering (single-quote patterns didn't match double-quote code).
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NB2 = ROOT / "notebooks" / "2 analysis - condition vegetation.ipynb"

# Targeted fixes: (context_string_nearby, wrong_FIG_ID, correct_FIG_ID)
# We use the label on the next line as context to ensure we fix the right cell.
FIXES = [
    # vegetation_response cell: label="fig7" → FIG_ID should be FIG_7
    ('label="fig7"',    '"FIG_6"',  '"FIG_7"'),
    # berm_condition cell: label="fig8" → FIG_ID should be FIG_8
    ('label="fig8"',    '"FIG_7"',  '"FIG_8"'),
    # pca_biplot cell: label="fig4" → FIG_ID should be FIG_4
    ('label="fig4"',    '"FIG_3"',  '"FIG_4"'),
    # veg_response_by_condition_texture cell: label="fig6" → FIG_ID should be FIG_6
    ('label="fig6"',    '"FIG_4"',  '"FIG_6"'),
]


def main():
    with open(NB2, "r", encoding="utf-8") as f:
        nb = json.load(f)

    fixes_applied = 0
    for cell in nb["cells"]:
        raw_src = cell.get("source", [])
        if isinstance(raw_src, str):
            src_text = raw_src
        else:
            src_text = "".join(raw_src)

        new_text = src_text
        for context, wrong, correct in FIXES:
            if context in new_text and wrong in new_text:
                new_text = new_text.replace(wrong, correct, 1)
                fixes_applied += 1
                print(f"  Fixed: {wrong} → {correct} (context: {context})")

        if new_text != src_text:
            cell["source"] = new_text.splitlines(keepends=True)
        else:
            cell["source"] = src_text.splitlines(keepends=True)

    with open(NB2, "w", encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False, indent=1)

    print(f"\n  ✓ {fixes_applied} FIG_ID marker(s) fixed")


if __name__ == "__main__":
    main()
