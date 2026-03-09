# Altar Valley Berms — AI Agent Instructions

> **Last updated:** 2026-03-06
> Read this file at the start of every new chat session.
> Update this file when new conventions, preferences, or project structure changes are established in chat.

---

## 1. Project Overview

Analysis of earthen berm (detention structure) outcomes in the Altar Valley, Arizona. The project evaluates berm structural integrity (intact vs degraded / breach / flank) and effectiveness across landforms (fan terraces, stream terraces, flood plains), soil textures, slope classes, and other predictors. Primary outputs are publication-ready figures and SI tables for two manuscripts (outcomes = structural integrity & vegetation response paper, failure_mechanisms = flanks & breaches paper).

### Workspace layout

```
project-root/
├── .github/copilot-instructions.md   ← THIS FILE
├── src/                               ← shared Python modules
│   ├── constants.py                   ← colour palettes, label dicts, orderings
│   ├── plotting.py                    ← matplotlib / seaborn helpers
│   ├── analysis.py                    ← stats helpers, GLM ranking, RF, SI formatters
│   ├── registry.py                    ← figure registry helpers
│   └── sda_access.py                  ← USDA SDA API utilities
├── notebooks/
│   ├── berm analysis with API.ipynb   ← primary analysis / figures
│   └── archive/                       ← old or dated notebooks
├── figures/
│   ├── outcomes/                      ← outcomes paper publication figures
│   ├── failure_mechanisms/            ← failure mechanisms paper publication figures
│   └── scratch/                       ← exploratory figures (never registered)
├── latex/
│   ├── figure_report_outcomes.tex     ← SI tables + figure list (outcomes)
│   ├── figure_report_failure_mechanisms.tex ← SI tables + figure list (failure mechanisms)
│   ├── figure_summary_outcomes.tex    ← figures-only summary PDF (outcomes)
│   └── figure_summary_failure_mechanisms.tex ← figures-only summary PDF (failure mechanisms)
└── data/
    ├── merged.csv                     ← primary dataset
    └── berm_exports/                  ← per-berm exported shapefiles
```

### Key variables

| Python name | Meaning |
|---|---|
| `data` | Primary DataFrame (one row per berm) |
| `df` | Filtered/derived working copy (varies by cell) |
| `LBL_EFFECTIVE` | Canonical label for the "effective" berm outcome |
| `lf_order` | Canonical landform display order |
| `fail_order` | Canonical Fail_Type display order |

---

## 2. Notebook Conventions

### Imports & sys.path

Cell 17 (id `95b17bbf`) adds `../src` to `sys.path` and imports all constants. Subsequent cells import from the four modules individually, e.g.:

```python
import sys as _sys
_sys.path.insert(0, '../src')
from constants import (LBL_EFFECTIVE, LF_COLORS, lf_order, ...)
from analysis import analyze_outcome, rank_predictors, PRETTY_LABELS, ...
from plotting import _draw_two_cat_panel, _draw_outcome_panel, ...
from registry import update_figure_registry, register_outcomes_figure, ...
```

### Python environment

- Python: `/Users/octaviacrompton/anaconda3/bin/python3` (conda `berms` env)
- Key packages: numpy, pandas, matplotlib, seaborn, scipy, statsmodels, scikit-learn, geopandas
- Virtual env: `berms` (defined in `environment.yml`)

### Cell structure preferences

- Keep one logical task per cell.
- Markdown cells before major sections.
- Use `df.copy()` before in-place mutations to avoid corrupting shared state.
- Prefer `_private` names (leading underscore) for cell-local temporaries.

### Feature toggles

[Document any boolean flags that change analysis behavior.]

```python
# Example:
USE_ALTERNATE = False   # When True, overwrite X with Y
```

---

## 3. Shared Code — `src/`

All reusable functions and constants live in the four modules below. **Do not duplicate these in notebook cells.** Notebooks import them by prepending `../src` to `sys.path` (done in cell 17).

### `src/constants.py`

Canonical colour palettes, label strings, and category orderings.

| Export | Type | Purpose |
|---|---|---|
| `INTACT_COL`, `DEGRADED_COL`, `BREACH_COL`, `FLANK_COL` | str | Hex colours for Fail_Type categories |
| `LF_COLORS`, `lf_order` | dict, list | Landform colours & display order |
| `LENGTH_COLORS`, `length_order` | dict, list | Berm length class colours & order |
| `SLOPE_COLORS`, `slope_order` | dict, list | Slope class colours & order |
| `CLAY_COLORS`, `clay_order` | dict, list | Clay content class colours & order |
| `SOILDEV_COLORS`, `soildev_order` | dict, list | Soil development colours & order |
| `LBL_EFFECTIVE`, `LBL_INEFFECTIVE`, `eff_order` | str, list | Effectiveness labels |
| `fail_order`, `fail_colors` | list, dict | Failure-type ordering and colours |
| `MODEL_CLR_CONDITION`, `MODEL_CLR_VEGRESPONSE`, `MODEL_CLR_CHANCE` | str | Model-outcome panel colours (condition vs veg response figures) |

When a new categorical variable needs canonical colours, add them here.

### `src/plotting.py`

Matplotlib / seaborn helpers.

| Export | Purpose |
|---|---|
| `width` | Module-level bar half-width constant (0.25) |
| `remove_legend_titles(obj)` | Strip legend titles from Axes / FacetGrid |
| `add_bar_edges(ax, lw)` | Add black outlines to bar patches |
| `_sig_stars(p)` | p → `"***"` / `"**"` / `"*"` / `"ns"` |
| `_fisher_one_sided(c_l, n_l, c_s, n_s)` | One-sided Fisher's exact in direction of observed difference |
| `_two_cat_metrics(df_sub, group_col, cat_a, cat_b)` | Fisher exact DataFrame for two-category integrity comparison |
| `_draw_two_cat_panel(ax, m, cat_a, cat_b, ...)` | Grouped-bar panel (two categories) |
| `_draw_multi_cat_panel(ax, df_sub, group_col, ...)` | Grouped-bar panel (multiple categories, optional pairwise brackets) |
| `_draw_outcome_panel(ax, result, lf_order, ..., lf_colors)` | Dot-plot with FDR-corrected significance brackets |

### `src/analysis.py`

Statistical analysis helpers.

| Export | Purpose |
|---|---|
| `chi2_with_cramers_v(ct)` | Chi-square + Cramér's V from a crosstab |
| `_two_prop_z(count1, n1, count2, n2)` | Two-proportion z-test |
| `_bh_adjust(pvals)` | Benjamini–Hochberg FDR correction |
| `pairwise_by_group(df, group_col, outcome_col, ...)` | All pairwise comparisons with FDR correction |
| `analyze_outcome(df, group_col, outcome_col, ...)` | Full chi-square + pairwise analysis dict |
| `_coerce_binary(y)` | Coerce outcome column to 0/1 float |
| `_collapse_rare_levels(s, ...)` | Collapse rare categories to "Other" |
| `_is_categorical(series, ...)` | Classify a series as categorical/numeric |
| `_fit_glm_pseudoR2(df, y, x, ...)` | Binomial GLM → McFadden R², Tjur R², LRT p |
| `_cv_auc(df, y, x, ...)` | Cross-validated AUC via logistic regression |
| `rank_predictors(df, y, predictors, ...)` | Rank all predictors by effect size |
| `fit_rf_binary(df, y, predictors, ...)` | Random Forest with CV metrics + permutation importance |
| `PRETTY_LABELS` | dict mapping column names → LaTeX-ready labels |
| `_clean_predictor_name(name, ...)` | Pretty-print a predictor name with fallback |
| `_format_ranking_for_si(ranked_df, ...)` | Prepare ranking DataFrame for SI CSV export (3 dp, drop type/n) |

### `src/registry.py`

Figure registry helpers.

| Export | Purpose |
|---|---|
| `update_figure_registry(fig_id, filename, ...)` | Main entry point — update both txt registries and LaTeX file |
| `register_outcomes_figure(fig_id, filename, ...)` | Wrapper for outcomes paper figures |
| `register_failure_mechanisms_figure(fig_id, filename, ...)` | Wrapper for failure mechanisms paper figures |
| `upsert_latex_figentry(tex_path, ...)` | Update a `\figentry{}` block in a .tex file |
| `_upsert_registry_block(path, fig_id, ...)` | Low-level upsert into plain-text registry |

### Adding new labels or colours

- New column labels → add to `PRETTY_LABELS` in `src/analysis.py`
- New category colours → add to the appropriate `*_COLORS` dict in `src/constants.py`
- Never duplicate these assignments inside a notebook cell

---

## 4. Figures & Figure Registry

### Two-tier figure system

1. **Publication figures** → saved to `figures/[batch]/`, named `fig<N>_<description>.png`
2. **Scratch/exploratory figures** → saved to `figures/[batch]/scratch/`, **never registered**

### Saving a publication figure

Every publication figure save must call `update_figure_registry()`:

```python
_fig_dir, _, _ = _fig_dirs()
_name = 'fig1_descriptive_name.png'
fig.savefig(_os.path.join(_fig_dir, _name), dpi=300, bbox_inches='tight')
update_figure_registry(
    'fig1', _name,
    description='Full multi-line description...',
    concise='Two-sentence summary. Key takeaway.')
```

### Saving a scratch figure

```python
_, _scratch, _ = _fig_dirs()
fig.savefig(_os.path.join(_scratch, 'name.png'), dpi=200, bbox_inches='tight')
# NO registry call
```

### Registry behaviour

- Accepts: `fig_id`, `filename`, `description` (full), `concise` (2 sentences: what + interpretation)
- Automatically re-sorts entries: main figures (fig1 → figN) first, SI figures at end
- Writes **two files** on every call:
  - `figure_registry.txt` — full detailed registry with metadata
  - `figure_registry_concise.txt` — short human-readable version
- Both files include: creation date, source notebook, figure save directory
- **Descriptions should be computed dynamically** from plot metrics (R², RMSE, etc.) so they stay current when data changes

### Registry entry format (full)

```
### fig1 ###
File     : fig1_descriptive_name.png
Updated  : YYYY-MM-DD HH:MM
Notebook : notebooks/[notebook].ipynb
Saved in : figures/[batch]
────────────────────────────────────────
<description with interpretation>
### end fig1 ###
```

### Registry entry format (concise)

```
Fig 1 — fig1_descriptive_name.png
  <Two sentences: description + key finding.>
```

### Figure numbering

- Main figures: `fig1`, `fig2`, `fig3`, … (sequential, in paper order)
- SI figures: `SI1`, `SI2`, … (sorted after main figures)
- Numbering should be stable; don't renumber existing figures without explicit request

### Figure style rules

- Use font-size constants from the shared module (`FS_LABEL`, `FS_TITLE`, etc.)
- Use `VAR_CMAPS` when colouring by a variable
- Use category colour/label dicts for categorical variables
- Metric annotations (RMSE, R², etc.): `ax.text()` in a corner, not in the title
- Legend style: prefer `Line2D` circle markers over `Patch` rectangles for scatter legends
- Truncate colormaps (e.g., 0.2–0.95) to avoid washed-out extremes near white
- Add small y-jitter when observed values cluster on discrete levels
- Use `renameit()` for axis labels whenever possible

---

## 5. LaTeX Figure Compilations

Each batch folder in `figures/` gets its own auto-generated LaTeX document.

### How it works

1. `latex/build_figure_doc.py` reads `figures/[batch]/figure_registry_concise.txt`
2. Generates `latex/[batch]_figures.tex` with one `\figure` per registry entry
3. Compiles to PDF with `pdflatex` (if installed); exits cleanly if not

### Usage

```bash
# One-shot build (all batches, or specify one)
python3 latex/build_figure_doc.py
python3 latex/build_figure_doc.py [batch_name]

# Auto-recompile .tex files on change (requires: brew install fswatch)
./latex/watch_latex.sh
```

### Conventions

- **Do not hand-edit** generated `.tex` files — they are overwritten on every build
- Figure labels match registry IDs: `\label{fig:fig1}`, `\label{fig:SI1}`, etc.
- One document per batch folder
- Concise registry caption → `\caption{…}`; empty captions fall back to filename
- New batch folders are auto-discovered when the build script runs with no args

---

## 6. Notebook File Management

- **Active notebooks** live in `notebooks/`.
- **Archived notebooks** go to `notebooks/archive/` with a date suffix if not already dated.
- Do not create new notebooks without being asked — modify existing ones.

---

## 7. Editing Preferences

- When editing `.ipynb` files, use `replace_string_in_file` with exact text matching (include 3–5 lines of context).
- For complex multi-line notebook cell edits that fail with text matching, fall back to a Python script using `json.load` / `json.dump`.
- Always use `df.copy()` before any operation that modifies a subset in-place.
- Prefer `_private` names (leading underscore) for cell-local temporaries to avoid polluting the kernel namespace.

---

## 8. Updating This File

**This file should be updated whenever:**
- A new shared convention is established (colour, font, label, file layout)
- A new figure is added to the registry numbering scheme
- LaTeX or manuscript conventions are established
- New shared code is added to `src/`
- File organization rules change

Add new sections or update existing ones. Keep the format consistent.
