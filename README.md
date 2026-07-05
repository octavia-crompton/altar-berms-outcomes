# Altar Valley Berm Outcomes

Analysis of earthen berm **structural condition** and **vegetation response** across the Altar Valley, southern Arizona. This repository supports a manuscript examining how soil properties, flow accumulation, berm geometry, and slope control (1) whether a berm remains intact or degrades and (2) the vegetation response near each berm, using landscape, soil, and remote sensing data for **775 water spreader berms**.

---

## Background

Earthen berms are widely used across rangelands in the southwestern United States to slow surface runoff, increase infiltration, reduce erosion, and support vegetation recovery. However, berms degrade over time — they can be *breached* (a break through the structure) or *flanked* (concentrated flow around the end of the berm) — and their effectiveness varies considerably across the landscape.

This project investigates how *soil properties*, *flow accumulation*, *slope*, *geomorphic position*, and *berm geometry* influence:

1. *Structural condition* — whether a berm remains **intact** or is **degraded** (breached or flanked)
2. *Vegetation response* — the upslope–downslope difference in satellite-derived vegetation greenness (SAVI) near each berm

The study area is the *Altar Valley*, a 247,000 ha semi-arid watershed in southern Arizona, USA, where more than 1,500 water spreader structures have been built since the early 1900s.

---

## Key Findings

- **Structural condition** is driven primarily by *berm length*, *flow accumulation*, and *soil texture*: shorter berms on finer-textured soils in areas of lower flow accumulation are more likely to remain intact.
- **Vegetation response** is better predicted by *slope* and *soil texture*: berms on steeper slopes and coarser (sandy loam) soils show larger upslope–downslope differences in greenness.
- Structural condition and vegetation response are **decoupled** — whether a berm is intact or degraded does not predict its vegetation response, suggesting the two outcomes are shaped by different environmental controls.
- Of 775 berms, **458 (59%) are intact** and **317 (41%) degraded** (203 flanked, 114 breached); **368 (47%)** exceed the ΔS = 7% vegetation-response threshold.
- *Landform* is not significantly associated with condition; the slope signal is modest on this gentle terrain but strengthens under a steeper (5%) threshold.

---

## Data

| Dataset | Source |
|---|---|
| Berm inventory (n = 775): structural condition, length, type | Nichols et al. (2021) |
| Landform, parent material, soil texture, profile development, chemistry (SAR/sodicity) | USDA NRCS Soil Survey (Web Soil Survey / SDA API) |
| LiDAR-derived slope and flow accumulation | Pima County Regional Flood Control District (2011, 2016) |
| Vegetation index (SAVI) | Sentinel-2 (10 m; 2016–2024) |

Vegetation response (ΔS) is the percent difference in median August–September SAVI between the upslope and downslope zones (15–60 m) of each berm, normalized by background SAVI. A berm is scored as showing a *vegetation response* when ΔS > 7% (see the threshold sensitivity notebooks below).

The primary analysis dataset is `data/merged.csv` (one row per berm).

---

## Repository Structure

```
├── src/
│   ├── constants.py       # colour palettes, label strings, category orderings
│   ├── plotting.py        # matplotlib/seaborn figure helpers
│   ├── analysis.py        # statistical analysis (chi-square, GLM, Random Forest, rankings, threshold scan)
│   ├── registry.py        # figure registry helpers
│   └── sda_access.py      # USDA Soil Data Access (SDA) API utilities
├── notebooks/
│   ├── 1 data processing - condition vegetation.ipynb   # assemble merged.csv (soils, chemistry, SAVI)
│   ├── 2 analysis - condition vegetation.ipynb          # main analysis + Figures 1–8
│   ├── 3 models - rf approaches.ipynb                   # Random Forest models & feature importance
│   ├── 4 analysis - controlled predictors.ipynb         # controlled-predictor regressions
│   ├── 5 analysis - sensitivity.ipynb                   # SAVI-threshold sensitivity (Figs. 7 & 8 statistics)
│   ├── 6 analysis - sensitivity fig7.ipynb              # full Figure 7 redrawn across thresholds
│   ├── gee-scripts.ipynb                                # Google Earth Engine SAVI extraction
│   └── models - *.ipynb                                 # auxiliary model exploration/comparison
├── figures/
│   ├── outcomes/          # publication figures (fig1–fig9) and SI figures/tables
│   ├── sensitivity/       # SAVI-threshold sensitivity renders (fig7/fig8 sweeps)
│   └── scratch/           # exploratory figures (not registered)
├── latex/
│   ├── figure_report_outcomes.tex    # SI figure list
│   ├── figure_summary_outcomes.tex   # figure captions / summaries
│   └── ...
├── draft/
│   ├── overleaf/         # read-only mirror of the Overleaf project (see draft/README.md)
│   └── archive/          # older dated manuscript drafts
├── data/
│   ├── merged.csv              # primary dataset (one row per berm)
│   └── ...
└── berm and landform shapefiles/
    ├── berm_structures_shapefile.*
    ├── fan_terraces_shapefile.*
    ├── stream_terraces_shapefile.*
    └── flood_plains_shapefile.*
```

---

## Methods Overview

### Predictor variables

Predictor variables are drawn from NRCS soil survey data and LiDAR-derived topography:

| Variable | Categories |
|---|---|
| Landform | Flood plains, Stream terraces, Fan terraces |
| Soil texture | Clay loam, Silt loam, Sandy loam, … (classes with n > 100) |
| Soil development | Weak (A-C profile) vs. Strong (Bt or Bk horizon present) |
| Clay content | ≤ 25% vs. > 25% |
| Sand content | ≤ 50% vs. > 50% |
| Flow accumulation | Low (< 2k contributing cells) vs. High (≥ 2k) |
| Berm length | ≤ 60 m vs. > 60 m |
| Slope | ≤ 2% vs. > 2% |

### Statistical approach

- Two-sided Fisher's exact and pairwise chi-square tests with Benjamini–Hochberg FDR correction
- Binomial GLM with McFadden R², Tjur R², and likelihood-ratio-test p-values
- Random Forest with cross-validated AUC and permutation importance
- PCA / EOF of the berm predictor space
- Predictor ranking by effect size across all variables
- **Threshold sensitivity**: the SAVI vegetation-response cut-off (default 7%) is swept from 0–10% to confirm that headline associations are threshold-independent (notebooks 5–6)

All reusable statistical functions are in `src/analysis.py`.

---

## Setup

### Requirements

```bash
conda env create -f environment.yml
conda activate berms
```

Key packages: `numpy`, `pandas`, `matplotlib`, `seaborn`, `scipy`, `statsmodels`, `scikit-learn`, `geopandas`.

### Running the analysis

Run the notebooks in order:

```
notebooks/1 data processing - condition vegetation.ipynb   # builds data/merged.csv
notebooks/2 analysis - condition vegetation.ipynb          # main analysis + Figures 1–8
notebooks/3 models - rf approaches.ipynb                   # Random Forest models
notebooks/4 analysis - controlled predictors.ipynb         # controlled-predictor regressions
notebooks/5 analysis - sensitivity.ipynb                   # threshold sensitivity (Figs. 7 & 8)
notebooks/6 analysis - sensitivity fig7.ipynb              # Figure 7 across thresholds
```

Notebook 1 requires network access (USDA SDA API and, for SAVI extraction, Google Earth Engine); notebooks 2–6 run offline from `data/merged.csv`. Publication figures are saved under `figures/outcomes/` and registered via `src/registry.py`; sensitivity renders are written to `figures/sensitivity/`.

### Manuscript

The manuscript is written on Overleaf; `draft/overleaf/` holds a read-only local mirror. Refresh it from the `overleaf` git remote — see `draft/README.md` for the workflow.

---

## Citation

*Manuscript in preparation.* Crompton, O., Nichols, M., Lapides, D.A. "Soil-geomorphic impact on berm structural condition and vegetation response in the US Southwest." *Catena* (in prep).

---

## Funding & Acknowledgements

USDA Agricultural Research Service, Southwest Watershed Research Center. Soil survey data provided by the USDA Natural Resources Conservation Service. LiDAR data provided by the Pima County Regional Flood Control District.
