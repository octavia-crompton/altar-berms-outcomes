"""
constants.py
============
Canonical colour palettes, display labels, and category orderings shared
across all notebooks and figures for the Altar Valley berm study.

Import with:
    from constants import (
        INTACT_COL, DEGRADED_COL, BREACH_COL, FLANK_COL,
        LF_COLORS, lf_order,
        LENGTH_COLORS, length_order,
        SLOPE_COLORS, slope_order,
        CLAY_COLORS, clay_order,
        SOILDEV_COLORS, soildev_order,
        LBL_EFFECTIVE, LBL_INEFFECTIVE, eff_order,
    )
"""

# ── Outcome / condition colours ──────────────────────────────────────────────
INTACT_COL   = "#5a8ab0"   # steel blue   – intact / no failure
DEGRADED_COL = "#e8d98a"   # pale yellow  – degraded (any failure)
BREACH_COL   = "#b86868"   # muted rose   – breach failure
FLANK_COL    = "#d4855a"   # terracotta   – flank failure

# ── Landform colours ─────────────────────────────────────────────────────────
LF_COLORS = {
    "Fan terraces":    "#c9a96e",   # warm tan
    "Flood plains":    "#6aabaa",   # teal
    "Stream terraces": "#4a87c0",   # steel blue
}
lf_order = ["Fan terraces", "Stream terraces", "Flood plains"]

# ── Berm length-class colours – blue-grey family ─────────────────────────────
LENGTH_COLORS = {
    "Short (≤ 50 m)": "#b8cfe0",   # pale blue-grey
    "Long (> 50 m)":  "#2e6899",   # deep steel blue
}
length_order = list(LENGTH_COLORS)

# ── Slope-class colours – earthy browns ─────────────────────────────────────
SLOPE_COLORS = {
    "Shallow (≤ 2%)": "#d8c3ac",   # pale mushroom
    "Steep (> 2%)":   "#8a5a3c",   # warm chestnut
}
slope_order = list(SLOPE_COLORS)

# ── Clay content colours – amber/golden-brown family ────────────────────────
CLAY_COLORS = {
    "Low clay":  "#f0d9a0",   # pale warm wheat
    "High clay": "#b5651d",   # medium sienna
}
clay_order = list(CLAY_COLORS)

# ── Soil development colours ──────────────────────────────────────────────────
SOILDEV_COLORS = {
    "B horizon":    "#5a9e6f",   # medium sage green – developed soil
    "No B horizon": "#c4a06b",   # warm tan/khaki    – weakly developed
}
soildev_order = list(SOILDEV_COLORS)

# ── Soil texture colours – earthy browns/tans, finest → coarsest ──────────
TEXTURE_COLORS = {
    "Clay loam":        "#7b5e3a",   # rich brown       – finest
    "Silt loam":        "#a07850",   # medium brown
    "Loam":             "#b89a6a",   # warm khaki
    "Sandy clay loam":  "#c9aa80",   # light khaki
    "Fine sandy loam":  "#d9bf98",   # pale tan
    "Sandy loam":       "#e8d4a8",   # pale sand
    "Loamy sand":       "#f0e0bc",   # very pale sand
    "Loamy coarse sand":"#f5ead0",   # lightest – coarsest
}
texture_order = list(TEXTURE_COLORS)

# ── Vegetation response display labels & colours ─────────────────────────────
LBL_EFFECTIVE   = "Vegetation response"
LBL_INEFFECTIVE = "No vegetation response"
eff_order = [LBL_EFFECTIVE, LBL_INEFFECTIVE]
eff_colors = {
    LBL_EFFECTIVE:   "#238b45",   # dark green   – vegetation response
    LBL_INEFFECTIVE: "#bae4b3",   # pale green   – no vegetation response
}

# ── Failure type ordering & colours ──────────────────────────────────────────
fail_order  = ["Intact", "Breach", "Flank"]
fail_colors = {
    "Intact": INTACT_COL,
    "Breach": BREACH_COL,
    "Flank":  FLANK_COL,
}

# ── Model-outcome panel colours (for figures comparing condition vs veg response models) ─
MODEL_CLR_CONDITION = "#4285bf"   # blue         – predicting berm condition
MODEL_CLR_VEGRESPONSE = "#72ab8d" # sage green   – predicting vegetation response
MODEL_CLR_CHANCE = "#aaaaaa"      # grey dashed  – chance baseline (AUC = 0.5)
