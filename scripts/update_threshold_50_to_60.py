#!/usr/bin/env python3
"""Update berm length threshold from 50 m to 60 m in all active notebooks.

Replacements are scoped to berm-length labels only — sand content "50%" is untouched.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# ── Replacement pairs (old → new) ──────────────────────────────────────────
REPLACEMENTS = [
    # Label strings
    ("Short (≤ 50 m)", "Short (≤ 60 m)"),
    ("Long (> 50 m)",  "Long (> 60 m)"),
    # Threshold value in code
    ("x <= 50 else",   "x <= 60 else"),
    ("thr = 50",       "thr = 60"),
    # Captions / comments in notebook markdown or code comments
    ("threshold 50 m", "threshold 60 m"),
]

NOTEBOOKS = [
    ROOT / "notebooks" / "1 data processing - condition vegetation.ipynb",
    ROOT / "notebooks" / "2 analysis - condition vegetation.ipynb",
    ROOT / "notebooks" / "analysis - flanks breaches port.ipynb",
    ROOT / "notebooks" / "analysis - flanks breaches.ipynb",
]

def update_notebook(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        nb = json.load(f)

    total_changes = 0
    for cell in nb["cells"]:
        # Always normalise source to list-of-lines (fixes any char-array corruption)
        raw_src = cell.get("source", [])
        if isinstance(raw_src, str):
            src_text = raw_src
        else:
            src_text = "".join(raw_src)

        new_text = src_text
        for old, new in REPLACEMENTS:
            if old in new_text:
                new_text = new_text.replace(old, new)

        if new_text != src_text:
            n = sum(1 for old, _ in REPLACEMENTS if old in src_text)
            total_changes += n
            cell["source"] = new_text.splitlines(keepends=True)
        else:
            # Still fix char-array corruption if present
            cell["source"] = src_text.splitlines(keepends=True)

    if total_changes:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(nb, f, ensure_ascii=False, indent=1)
        print(f"  ✓ {path.name}: {total_changes} replacement(s)")
    else:
        print(f"  – {path.name}: no changes needed")

    return total_changes

def main():
    print("Updating berm length threshold 50 → 60 m in notebooks…\n")
    total = 0
    for nb_path in NOTEBOOKS:
        if not nb_path.exists():
            print(f"  ✗ {nb_path.name}: NOT FOUND")
            continue
        total += update_notebook(nb_path)
    print(f"\nDone. {total} total replacement(s) across {len(NOTEBOOKS)} notebooks.")

if __name__ == "__main__":
    main()
