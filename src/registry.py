"""
registry.py
===========
Figure registry helpers for idempotent updating of:
  - plain-text figure registries (full and concise)
  - LaTeX \figentry blocks in figure report .tex files

Import with:
    from registry import (
        register_outcomes_figure,
        register_failure_mechanisms_figure,
        upsert_latex_figentry,
        update_figure_registry,
    )
"""

from pathlib import Path
from datetime import datetime
import re

# ── Paths to the LaTeX report files ──────────────────────────────────────────
# These are relative to the project root; at notebook runtime they are resolved
# relative to the notebooks/ folder so we prepend ../
OUTCOMES_TEX = Path("../latex/figure_report_outcomes.tex")
FAILURE_MECHANISMS_TEX = Path("../latex/figure_report_failure_mechanisms.tex")

# Backward-compatible aliases
PAPER1_TEX = OUTCOMES_TEX
PAPER2_TEX = FAILURE_MECHANISMS_TEX


# ── Plain-text registry ───────────────────────────────────────────────────────

def _upsert_registry_block(
    path, label, file_name, updated, stats_text, interpretation_text,
    concise=False
):
    """Idempotently insert/replace a named block in a plain-text registry file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        text = path.read_text(encoding="utf-8")
    else:
        title = "FIGURE REGISTRY (CONCISE)" if concise else "FIGURE REGISTRY"
        text = (
            "=" * 80 + "\n"
            + f"{title}\n"
            + "Altar Valley Berms\n"
            + "=" * 80 + "\n"
            + "=" * 80 + "\n"
        )

    text = text.replace(
        "(No figures registered yet. Add entries below as figures are created.)\n", ""
    )

    sep_line = "\u2500" * 72
    if concise:
        stats_line = " ".join(str(stats_text).split())
        interp_line = " ".join(str(interpretation_text).split())
        block = (
            f"### {label} ###\n"
            f"File    : {file_name}\n"
            f"Updated : {updated}\n"
            f"{sep_line}\n"
            f"Stats   : {stats_line}\n"
            f"Interpretation: {interp_line}\n"
            f"### end {label} ###\n\n"
        )
    else:
        block = (
            f"### {label} ###\n"
            f"File    : {file_name}\n"
            f"Updated : {updated}\n"
            f"{sep_line}\n"
            f"Statistical test:\n{stats_text}\n\n"
            f"Interpretation:\n{interpretation_text}\n"
            f"### end {label} ###\n\n"
        )

    patt = rf"### {re.escape(label)} ###.*?### end {re.escape(label)} ###\n"
    if re.search(patt, text, flags=re.S):
        text = re.sub(patt, lambda _: block, text, count=1, flags=re.S)
    else:
        sep = "=" * 80
        idx = text.rfind(sep)
        if idx != -1:
            text = text[:idx].rstrip() + "\n" + block + sep + "\n"
        else:
            text = text.rstrip() + "\n" + block

    path.write_text(text, encoding="utf-8")


def _update_txt_registries(paper_dir, label, file_name, updated, stats_text, interpretation_text):
    """Write/update both full and concise .txt registries for a paper."""
    base = Path(paper_dir)
    _upsert_registry_block(
        base / "figure_registry.txt",
        label, file_name, updated, stats_text, interpretation_text, concise=False,
    )
    _upsert_registry_block(
        base / "figure_registry_concise.txt",
        label, file_name, updated, stats_text, interpretation_text, concise=True,
    )


# ── LaTeX \figentry upsert ────────────────────────────────────────────────────

def upsert_latex_figentry(
    latex_path, tag, label, file_name, updated, stats_text, interpretation_text
):
    """Idempotently insert/replace a \\figentry block between %% TAG_START/END markers."""
    latex_path = Path(latex_path)
    if not latex_path.exists():
        print(f"WARNING: {latex_path} not found — skipping upsert")
        return

    text = latex_path.read_text(encoding="utf-8")

    block_content = (
        f"\\figentry%\n"
        f"  {{{label}}}%\n"
        f"  {{{file_name}}}%\n"
        f"  {{{updated}}}%\n"
        f"  {{{stats_text}}}%\n"
        f"  {{{interpretation_text}}}\n"
    )

    start_marker = f"%% {tag}_START"
    end_marker   = f"%% {tag}_END"

    patt = re.compile(
        rf"^{re.escape(start_marker)}\n.*?^{re.escape(end_marker)}$",
        re.MULTILINE | re.DOTALL,
    )
    replacement = f"{start_marker}\n{block_content}{end_marker}"

    if patt.search(text):
        text = patt.sub(lambda _m: replacement, text, count=1)
    else:
        text = text.replace(
            "\\end{document}",
            f"\n{replacement}\n\n\\end{{document}}",
        )

    text = re.sub(rf"({re.escape(end_marker)})\n(?!\n)", rf"\1\n\n", text)
    latex_path.write_text(text, encoding="utf-8")
    print(f"Updated \u2192 {latex_path}  ({label})")


# ── Paper-specific convenience wrappers ──────────────────────────────────────

def register_outcomes_figure(tag, label, file_name, stats_text, interpretation_text, updated=None):
    """Register/update a figure in the Outcomes paper LaTeX report + .txt registries."""
    updated = updated or datetime.now().strftime("%Y-%m-%d %H:%M")
    upsert_latex_figentry(OUTCOMES_TEX, tag, label, file_name, updated, stats_text, interpretation_text)
    _update_txt_registries("../figures/outcomes", label, file_name, updated, stats_text, interpretation_text)

# Backward-compatible alias
register_paper1_figure = register_outcomes_figure


def register_failure_mechanisms_figure(label, file_name, stats_text, interpretation_text, updated=None):
    """Register/update a figure in the Failure Mechanisms paper LaTeX report + .txt registries."""
    updated = updated or datetime.now().strftime("%Y-%m-%d %H:%M")

    m = re.match(r"fig(\d+)", label)
    tag = f"FIG_{m.group(1)}" if m else label.upper().replace(" ", "_")

    upsert_latex_figentry(
        FAILURE_MECHANISMS_TEX, tag,
        f"Figure {m.group(1)}" if m else label,
        file_name, updated, stats_text, interpretation_text,
    )
    _update_txt_registries("../figures/failure_mechanisms", label, file_name, updated, stats_text, interpretation_text)
    print(f"Updated: ../figures/failure_mechanisms/figure_registry.txt")
    print(f"Updated: ../figures/failure_mechanisms/figure_registry_concise.txt")

# Backward-compatible alias
register_paper2_figure = register_failure_mechanisms_figure


# ── Generic per-paper registry helper used by older cells ────────────────────

def update_figure_registry(fig_id, filename, description, concise,
                            paper_dir="../figures/failure_mechanisms",
                            notebook="notebooks/ berm analysis with API.ipynb"):
    """Legacy helper kept for backward compatibility."""
    updated = datetime.now().strftime("%Y-%m-%d %H:%M")
    _update_txt_registries(paper_dir, fig_id, filename, updated, description, concise)
