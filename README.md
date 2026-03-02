# Altar Valley Berm Outcomes

Analysis of earthen berm structural condition and vegetation response across the Altar Valley, southern Arizona. This repository supports two companion manuscripts examining (1) the controls on berm structural integrity and (2) the controls on berm-driven vegetation response, using landscape, soil, and remote sensing data for 550 water spreader berms.

---

## Background

Earthen berms are widely used across rangelands in the southwestern United States to slow surface runoff, increase infiltration, reduce erosion, and support vegetation recovery. However, berms degrade over time — they can be **breached** (a break through the structure) or **flanked** (concentrated flow around the end of the berm) — and their effectiveness varies considerably across the landscape.

This project investigates how **geomorphic position**, **soil properties**, **slope**, and **berm geometry** influence:
1. **Structural condition** — whether a berm remains intact, is breached, or is flanked
2. **Vegetation response** — the upslope–downslope difference in satellite-derived vegetation greenness (SAVI) near each berm

The study area is the **Altar Valley**, a 247,000 ha semi-arid watershed in southern Arizona, USA.

---

## Key Findings

- Berms on **fan terraces** with well-developed soils (Bt/Bk horizons) are significantly more likely to remain intact and show greater upslope vegetation greenness
- Berms on **flood plains** have higher breach rates and show smaller upslope–downslope vegetation differences
- **Stream terraces** exhibit intermediate behavior, reflecting their transitional geomorphic position
- **Longer berms** (> 50 m) and **steeper slopes** (> 2%) are associated with higher failure rates
- Berm structural condition and vegetation response are **not tightly coupled** — intact berms do not always produce strong vegetation responses, and vice versa
- **Soil development** (presence of B horizons) is a consistent cross-cutting predictor of both berm stability and vegetation response

---

## Data

| Dataset | Source |
|---|---|
| Berm inventory (n = 550): structural condition, length, type | Nichols et al. (2021) |
| Landform, parent material, soil texture, profile development | USDA NRCS Soil Survey (Web Soil Survey / SDA API) |
| LiDAR-derived slope | Pima County Regional Flood Control District (2011, 2016) |
| Vegetation index (SAVI) | Sentinel-2 (10 m; 2016–2024) |

Vegetation response ($\Delta S$) is computed as the percent difference in median August–September SAVI between the upslope and downslope zones (15–60 m) of each berm, normalized by background SAVI.

The primary analysis dataset is `data/merged.csv` (one row per berm).

---

## Repository Structure

```
├── src/
│   ├── constants.py       # colour palettes, label strings, category orderings
│   ├── plotting.py        # matplotlib/seaborn figure helpers
│   ├── analysis.py        # statistical analysis (chi-square, GLM, Random Forest, rankings)
│   ├── registry.py        # figure registry helpers
│   └── sda_access.py      # USDA Soil Data Access (SDA) API utilities
├── notebooks/
│   ├── berm analysis - paper1 condition vegetation.ipynb   # paper 1 analysis and figures
│   ├── berm analysis - paper2 flanks breaches.ipynb        # paper 2 analysis and figures
│   └── archive/           # dated snapshots of earlier notebook versions
├── figures/
│   ├── paper1/            # publication figures (paper 1)
│   ├── paper2/            # publication figures (paper 2)
│   └── scratch/           # exploratory figures (not registered)
├── latex/
│   ├── figure_report_paper1.tex   # SI tables and figure list (paper 1)
│   ├── figure_report_paper2.tex   # SI tables and figure list (paper 2)
│   └── ...
├── data/
│   ├── merged.csv              # primary dataset
│   └── berm_exports/           # per-berm shapefiles
└── berm and landform shapefiles/
    ├── berm_structures_shapefile.*
    ├── fan_terraces_shapefile.*
    ├── stream_terraces_shapefile.*
    └── flood_plains_shapefile.*
```

---

## Methods Overview

### Predictor variables

All predictor variables are drawn from NRCS soil survey data and LiDAR-derived topography:

| Variable | Categories |
|---|---|
| Landform | Flood plains, Stream terraces, Fan terraces |
| Parent material | Fine/coarse-textured alluvium; Mixed alluvium; Granite/schist-derived alluvium |
| Soil development | Weak (A-C profile) vs. Strong (Bt or Bk horizon present) |
| Clay content | ≤ 25% vs. > 25% |
| Sand content | ≤ 50% vs. > 50% |
| Berm length | ≤ 50 m vs. > 50 m |
| Slope | ≤ 2% vs. > 2% |

### Statistical approach

- Pairwise chi-square tests with Benjamini–Hochberg FDR correction
- Binomial GLM with McFadden R², Tjur R², and likelihood ratio test p-values
- Random Forest with cross-validated AUC and permutation importance
- Predictor ranking by effect size across all variables

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

Open and run the notebooks in order:

```
notebooks/berm analysis - paper1 condition vegetation.ipynb
notebooks/berm analysis - paper2 flanks breaches.ipynb
```

Publication figures are saved to `figures/paper1/` and `figures/paper2/` and registered in `figure_registry.txt` files within those directories.

---

## Citation

*Manuscript in preparation.* Crompton, O., Nichols, M., Lapides, D.A. "Soil-geomorphic impact on berm structural condition and vegetation response in the US Southwest." *Catena* (in prep).

---

## Funding & Acknowledgements

USDA Agricultural Research Service, Southwest Watershed Research Center. Soil survey data provided by the USDA Natural Resources Conservation Service. LiDAR data provided by the Pima County Regional Flood Control District.
