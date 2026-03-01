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

# ── Slope-class colours – dusty rose/burgundy family ────────────────────────
SLOPE_COLORS = {
    "Shallow (≤ 2%)": "#e8d4d6",   # pale dusty rose
    "Steep (> 2%)":   "#8b4358",   # deep muted burgundy
}
slope_order = list(SLOPE_COLORS)

# ── Clay content colours – amber/golden-brown family ────────────────────────
CLAY_COLORS = {
    "Low clay":  "#f0d9a0",   # pale warm wheat
    "High clay": "#b5651d",   # medium sienna
}
clay_order = list(CLAY_COLORS)

# ── Soil development colours – olive/sage family ─────────────────────────────
SOILDEV_COLORS = {
    "No B horizon": "#d5d9be",   # pale sage green – weak development
    "B horizon":    "#5a6b2a",   # deep olive      – stronger development
}
soildev_order = list(SOILDEV_COLORS)

# ── Vegetation response display labels ───────────────────────────────────────
LBL_EFFECTIVE   = "Vegetation response"
LBL_INEFFECTIVE = "No vegetation response"
eff_order = [LBL_EFFECTIVE, LBL_INEFFECTIVE]

# ── Failure type ordering & colours ──────────────────────────────────────────
fail_order  = ["Intact", "Breach", "Flank"]
fail_colors = {
    "Intact": INTACT_COL,
    "Breach": BREACH_COL,
    "Flank":  FLANK_COL,
}
