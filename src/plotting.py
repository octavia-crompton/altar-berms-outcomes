"""
plotting.py
-----------
Reusable matplotlib / seaborn helpers for the berm-outcomes analysis.

Functions
---------
remove_legend_titles(obj)
    Remove legend titles from Axes, arrays of Axes, or Seaborn FacetGrids.

add_bar_edges(ax, lw=0.8)
    Add black edges to all bar patches in an Axes.

_sig_stars(p)
    Convert a p-value to significance stars ("***", "**", "*", "ns").

_fisher_one_sided(c_l, n_l, c_s, n_s)
    One-sided Fisher's exact test in the direction of the observed difference.

_two_cat_metrics(df_sub, group_col, cat_a, cat_b)
    Fisher exact for intact/degraded rate between two binary categories.

_draw_two_cat_panel(ax, m, cat_a, cat_b, colors, legend_title, title)
    Grouped-bar panel for two categories.

_draw_multi_cat_panel(ax, df_sub, group_col, cat_order, cat_colors, title, pairwise=False)
    Grouped-bar panel for multiple categories.

_draw_outcome_panel(ax, result, lf_order, title, ylabel)
    Dot-plot panel with FDR-corrected significance brackets.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as _mticker
import seaborn as sns
from scipy.stats import fisher_exact
from itertools import combinations as _combinations

# Module-level constant used by panel helpers
width = 0.25  # bar half-width for 2-category panels


# ---------------------------------------------------------------------------
# Legend helpers
# ---------------------------------------------------------------------------

def remove_legend_titles(obj):
    """
    Remove legend titles from:
      - a single Matplotlib Axes,
      - an iterable of Axes (e.g., np.ndarray from plt.subplots),
      - or a Seaborn FacetGrid/AxisGrid.
    """
    def _clear(ax):
        leg = ax.get_legend()
        if leg is not None:
            leg.set_title(None)

    # Seaborn FacetGrid / AxisGrid
    if hasattr(obj, "axes") and hasattr(obj, "fig"):
        for ax in np.ravel(obj.axes):
            _clear(ax)
        return obj

    # Single Axes
    if hasattr(obj, "get_legend") and callable(obj.get_legend):
        _clear(obj)
        return obj

    # Iterable of Axes
    try:
        for ax in obj:
            _clear(ax)
        return obj
    except TypeError:
        raise TypeError(
            "Expected an Axes, iterable of Axes, or a Seaborn FacetGrid/AxisGrid."
        )


# ---------------------------------------------------------------------------
# Bar helpers
# ---------------------------------------------------------------------------

def add_bar_edges(ax, lw=0.8):
    """Add black edges to all bar patches in an Axes."""
    for p in ax.patches:
        p.set_edgecolor("black")
        p.set_linewidth(lw)


# ---------------------------------------------------------------------------
# Significance helpers
# ---------------------------------------------------------------------------

def _sig_stars(p):
    """Return significance stars for a p-value."""
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    return "ns"


def _fisher_one_sided(c_l, n_l, c_s, n_s):
    """One-sided Fisher's exact test in the direction of the observed difference."""
    table = [[c_l, n_l - c_l], [c_s, n_s - c_s]]
    p_l, p_s = c_l / n_l, c_s / n_s
    direction = "greater" if p_l >= p_s else "less"
    _, p = fisher_exact(table, alternative=direction)
    return p, direction


# ---------------------------------------------------------------------------
# Two-category metrics
# ---------------------------------------------------------------------------

def _two_cat_metrics(df_sub, group_col, cat_a, cat_b):
    """Fisher exact for intact/degraded rate between two categories."""
    d = df_sub.dropna(subset=[group_col]).copy()
    d["_failed"] = d["Fail_Type"].ne("Intact")
    n_a = (d[group_col] == cat_a).sum()
    n_b = (d[group_col] == cat_b).sum()
    rows = {}
    for metric, is_intact in [("Intact", True), ("Degraded", False)]:
        mask = d["_failed"].eq(not is_intact)
        c_a = mask[d[group_col] == cat_a].sum()
        c_b = mask[d[group_col] == cat_b].sum()
        p_a, p_b = c_a / n_a, c_b / n_b
        direction = "greater" if p_a >= p_b else "less"
        _, p_val = fisher_exact(
            [[c_a, n_a - c_a], [c_b, n_b - c_b]], alternative=direction
        )
        rows[metric] = {cat_a: p_a, cat_b: p_b, "sig": _sig_stars(p_val)}
    import pandas as pd
    return pd.DataFrame(rows).T


# ---------------------------------------------------------------------------
# Panel drawing helpers
# ---------------------------------------------------------------------------

def _draw_two_cat_panel(ax, m, cat_a, cat_b, colors, legend_title, title):
    """Grouped-bar panel for two categories (Intact vs Degraded)."""
    outcomes = ["Intact", "Degraded"]
    x = np.arange(2)
    for cat, offset in [(cat_a, -width / 2), (cat_b, width / 2)]:
        vals = [m.loc[o, cat] for o in outcomes]
        ax.bar(
            x + offset, vals, width, label=cat,
            color=colors[cat], edgecolor="black", linewidth=0.7,
        )
    for i, o in enumerate(outcomes):
        sig = m.loc[o, "sig"]
        top = max(m.loc[o, cat_a], m.loc[o, cat_b]) + 0.03
        bh = 0.015
        ax.plot(
            [x[i] - width / 2, x[i] - width / 2, x[i] + width / 2, x[i] + width / 2],
            [top, top + bh, top + bh, top],
            lw=1, color="black",
        )
        col = "black" if sig != "ns" else "#888888"
        ax.text(
            x[i], top + bh + 0.005, sig,
            ha="center", va="bottom", fontsize=13, color=col,
            fontweight="bold" if sig != "ns" else "normal",
        )
    ax.set_xticks(x)
    ax.set_xticklabels(outcomes)
    ax.set_ylabel("Proportion of berms")
    ax.set_title(title)
    ax.set_ylim(0, 1.0)
    ax.yaxis.set_major_formatter(_mticker.FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax.legend(title=legend_title, frameon=False, fontsize=11, loc="upper right")
    sns.despine(ax=ax)


def _draw_multi_cat_panel(ax, df_sub, group_col, cat_order, cat_colors, title, pairwise=False):
    """Grouped-bar panel: Intact / Degraded x-axis, one bar per category."""
    from scipy.stats import chi2_contingency

    d = df_sub.dropna(subset=[group_col]).copy()
    d["_outcome"] = d["Fail_Type"].apply(
        lambda x: "Intact" if x == "Intact" else "Degraded"
    )
    cats = [c for c in cat_order if c in d[group_col].unique()]
    n_cats = len(cats)
    bar_w = width
    _mc_w = n_cats * bar_w
    offsets = np.linspace(-_mc_w / 2 + bar_w / 2, _mc_w / 2 - bar_w / 2, n_cats)
    outcomes = ["Intact", "Degraded"]
    x = np.arange(len(outcomes))

    bars_data = {}
    ns_cat = {}
    for cat in cats:
        sub = d[d[group_col] == cat]
        n = len(sub)
        ns_cat[cat] = n
        bars_data[cat] = {
            "Intact":   (sub["_outcome"] == "Intact").sum() / n,
            "Degraded": (sub["_outcome"] == "Degraded").sum() / n,
        }

    import pandas as pd
    ct_chi = pd.crosstab(d[group_col], d["_outcome"]).reindex(cats).dropna()
    p_chi: float = chi2_contingency(ct_chi)[1]  # type: ignore[index]
    p_str = f"p = {p_chi:.3g}" if p_chi >= 0.001 else "p < 0.001"

    for ci, (cat, offset) in enumerate(zip(cats, offsets)):
        for oi, outcome in enumerate(outcomes):
            ax.bar(
                x[oi] + offset, bars_data[cat][outcome], bar_w,
                color=cat_colors.get(cat, "#aaaaaa"), edgecolor="black", linewidth=0.5,
                label=cat if oi == 0 else "_nolegend_",
            )

    bh = 0.015

    if pairwise:
        pair_list = list(_combinations(range(n_cats), 2))
        pair_list.sort(key=lambda p: abs(offsets[p[1]] - offsets[p[0]]))
        global_y_max = 0
        for oi, outcome in enumerate(outcomes):
            current_top = max(bars_data[cat][outcome] for cat in cats) + 0.03
            for ci, cj in pair_list:
                ca, cb = cats[ci], cats[cj]
                na, nb = ns_cat[ca], ns_cat[cb]
                ka = (d[d[group_col] == ca]["_outcome"] == outcome).sum()
                kb = (d[d[group_col] == cb]["_outcome"] == outcome).sum()
                p_a, p_b = ka / na, kb / nb
                direction = "greater" if p_a >= p_b else "less"
                _, p_pair = fisher_exact(
                    [[ka, na - ka], [kb, nb - kb]], alternative=direction
                )
                sig = _sig_stars(p_pair)
                x_left = x[oi] + offsets[ci]
                x_right = x[oi] + offsets[cj]
                y_base = max(bars_data[ca][outcome], bars_data[cb][outcome])
                y_start = max(y_base + 0.02, current_top)
                ax.plot(
                    [x_left, x_left, x_right, x_right],
                    [y_start, y_start + bh, y_start + bh, y_start],
                    lw=0.9, color="black" if sig != "ns" else "#bbbbbb",
                )
                col = "black" if sig != "ns" else "#aaaaaa"
                ax.text(
                    (x_left + x_right) / 2, y_start + bh + 0.003, sig,
                    ha="center", va="bottom", fontsize=11, color=col,
                    fontweight="bold" if sig != "ns" else "normal",
                )
                current_top = y_start + bh + 0.025
            global_y_max = max(global_y_max, current_top)
        y_max = global_y_max + 0.04  # noqa: F841 (used implicitly for future ylim)
    else:
        sig_overall = _sig_stars(p_chi)
        for oi in range(2):
            vals = [bars_data[cat][outcomes[oi]] for cat in cats]
            top = max(vals) + 0.03
            ax.plot(
                [x[oi] - _mc_w / 2, x[oi] - _mc_w / 2, x[oi] + _mc_w / 2, x[oi] + _mc_w / 2],
                [top, top + bh, top + bh, top],
                lw=1, color="black",
            )
            col = "black" if sig_overall != "ns" else "#888888"
            ax.text(
                x[oi], top + bh + 0.005, sig_overall,
                ha="center", va="bottom", fontsize=13, color=col,
                fontweight="bold" if sig_overall != "ns" else "normal",
            )

    ax.set_xticks(x)
    ax.set_xticklabels(outcomes)
    ax.set_ylabel("Proportion of berms")
    ax.set_title(f"{title}\n({p_str})", fontsize=12)
    ax.set_ylim(0, 1.0)
    ax.yaxis.set_major_formatter(_mticker.FuncFormatter(lambda v, _: f"{v:.0%}"))
    ax.legend(frameon=False, fontsize=11, loc="upper right")
    sns.despine(ax=ax)


def _draw_outcome_panel(ax, result, lf_order, title, ylabel, lf_colors):
    """Dot plot with FDR-corrected significance brackets for one outcome.

    Parameters
    ----------
    ax : matplotlib.axes.Axes
    result : dict
        Output of ``analyze_outcome`` (keys: proportions, pairwise, global).
    lf_order : list[str]
        Ordered list of landform labels.
    title : str
    ylabel : str
    lf_colors : dict
        Mapping from landform label to hex colour string.
    """
    props = result["proportions"].reindex(lf_order)
    pw = result["pairwise"]
    g_stats = result["global"]

    # --- dots ---
    y_vals = props.values
    x_vals = np.arange(len(lf_order))
    for xi, lf in enumerate(lf_order):
        col = lf_colors.get(lf, "#aaaaaa")
        ax.scatter(
            xi, y_vals[xi], color=col, s=220, zorder=3,
            edgecolors="white", linewidths=0.8,
        )

    # --- significance brackets (FDR-significant pairs only) ---
    sig_pw = pw[pw["significant"]].copy()
    sig_pw = sig_pw.assign(
        _base=sig_pw.apply(
            lambda r: max(props.get(r["group_a"], 0), props.get(r["group_b"], 0)),
            axis=1,
        )
    ).sort_values("_base")

    current_top = -1.0
    for _, row in sig_pw.iterrows():
        xa = lf_order.index(row["group_a"])
        xb = lf_order.index(row["group_b"])
        ya = props.get(row["group_a"], 0)
        yb = props.get(row["group_b"], 0)
        bracket_y = max(max(ya, yb) + 0.05, current_top + 0.06)
        ax.plot([xa, xa], [ya, bracket_y], color="black", lw=0.8)
        ax.plot([xb, xb], [yb, bracket_y], color="black", lw=0.8)
        ax.plot([xa, xb], [bracket_y, bracket_y], color="black", lw=0.8)
        q_val = row["q_fdr"]
        stars = "***" if q_val < 0.001 else "**" if q_val < 0.01 else "*"
        ax.text(
            (xa + xb) / 2, bracket_y + 0.005, stars,
            ha="center", va="bottom", fontsize=9, fontweight="bold",
        )
        current_top = bracket_y + 0.04

    p_str = (
        f"p = {g_stats['p_value']:.3g}" if g_stats["p_value"] >= 0.001 else "p < 0.001"
    )
    ax.set_title(
        f"{title}\n{p_str}, Cramér's V = {g_stats['cramers_v']:.2f}", fontsize=10
    )
    ax.set_xticks(x_vals)
    ax.set_xticklabels(lf_order, rotation=15, ha="right")
    ax.set_ylabel(ylabel)
    ax.set_ylim(0.20, 0.80)
    ax.yaxis.set_major_formatter(_mticker.FuncFormatter(lambda v, _: f"{v:.0%}"))
    sns.despine(ax=ax)
