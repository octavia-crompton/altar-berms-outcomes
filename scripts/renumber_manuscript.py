#!/usr/bin/env python3
"""Shift all figN (N≥2) → fig(N+1) in the manuscript, and insert a new fig2 block.

Handles: \ref{fig:figN}, \label{fig:figN}, \includegraphics filenames.
"""
import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEX_FILES = [
    ROOT / "draft" / "local" / "main.tex",
    ROOT / "draft" / "overleaf" / "main.tex",
]

# --- shift fig references: fig{N} → fig{N+1} for N ≥ 2 ---

def _shift_ref(m):
    """Shift \\ref{fig:figN} where N ≥ 2."""
    n = int(m.group(1))
    return f"\\ref{{fig:fig{n+1}}}" if n >= 2 else m.group(0)

def _shift_label(m):
    """Shift \\label{fig:figN} where N ≥ 2."""
    n = int(m.group(1))
    return f"\\label{{fig:fig{n+1}}}" if n >= 2 else m.group(0)

# Map of old includegraphics filenames → new (ordered high to low)
FILENAME_MAP = [
    ("fig7_veg_response_by_condition_texture.png", "fig8_veg_response_by_condition_texture.png"),
    ("fig6_vegetation_response.png",               "fig7_vegetation_response.png"),
    ("fig5_berm_condition.png",                     "fig6_berm_condition.png"),
    ("fig4_pca_biplot.png",                         "fig5_pca_biplot.png"),
    ("fig3_controlled_predictors.png",              "fig4_controlled_predictors.png"),
    ("fig2_model_performance_importance.png",        "fig3_model_performance_importance.png"),
]

# New fig2 block to insert (after the fig1 figure environment)
NEW_FIG2_BLOCK = r"""
\begin{figure}[htb!]
\centering
\includegraphics[width=\textwidth]{fig2_veg_response.pdf}
\caption{Vegetation response metric for an example berm. (A)~Upslope, downslope, and background area delineation. (B)~SAVI values in these three areas. (C)~Monthly climatology of SAVI showing the upslope--downslope contrast used to compute $\Delta S$.}
\label{fig:fig2}
\end{figure}
"""


def process(text: str) -> str:
    # 1. Shift \ref{fig:figN}  (N ≥ 2)
    text = re.sub(r'\\ref\{fig:fig(\d+)\}', _shift_ref, text)
    # 2. Shift \label{fig:figN} (N ≥ 2)
    text = re.sub(r'\\label\{fig:fig(\d+)\}', _shift_label, text)
    # 3. Shift includegraphics filenames (high → low order)
    for old_fn, new_fn in FILENAME_MAP:
        text = text.replace(old_fn, new_fn)
    # 4. Insert new fig2 block after the fig1 figure environment
    # Find \label{fig:fig1} ... \end{figure} and insert after it
    pattern = r'(\\label\{fig:fig1\}\s*\\end\{figure\})'
    m = re.search(pattern, text)
    if m:
        insert_pos = m.end()
        text = text[:insert_pos] + NEW_FIG2_BLOCK + text[insert_pos:]
    else:
        print("  WARNING: could not find fig1 end-of-figure to insert fig2 block")
    return text


def main():
    for tex_path in TEX_FILES:
        if not tex_path.exists():
            print(f"  ✗ {tex_path}: not found")
            continue
        original = tex_path.read_text(encoding="utf-8")
        updated = process(original)
        if updated != original:
            tex_path.write_text(updated, encoding="utf-8")
            # Count changes
            ref_shifts = len(re.findall(r'\\ref\{fig:fig[3-9]\}', updated))
            label_shifts = len(re.findall(r'\\label\{fig:fig[3-9]\}', updated))
            print(f"  ✓ {tex_path.relative_to(ROOT)}: updated ({ref_shifts} refs, {label_shifts} labels)")
        else:
            print(f"  – {tex_path.relative_to(ROOT)}: no changes")


if __name__ == "__main__":
    main()
