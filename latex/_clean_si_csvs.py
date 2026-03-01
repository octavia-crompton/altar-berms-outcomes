import pandas as pd
from pathlib import Path

PRETTY_LABELS = {
    "slope_200":          "Hillslope gradient (200 m)",
    "slope_100":          "Hillslope gradient (100 m)",
    "Shape_Leng":         "Berm length",
    "FA_30_max":          "Flow accumulation (30 m)",
    "Landform":           "Landform",
    "Texture":            "Soil texture",
    "ParentMaterial":     "Parent material",
    "Soil_Development":   "Soil development",
    "Berm_Length_Class":  "Berm length class",
    "TypicalProfile":     "Typical soil profile",
    "claytotal_r":        "Clay content (r-horizon, %)",
    "sandtotal_r":        "Sand content (r-horizon, %)",
    "silttotal_r":        "Silt content (r-horizon, %)",
    "surf_claybg":        "Surface clay (%)",
    "surf_sandbg":        "Surface sand (%)",
    "surfsoc_background": "Surface organic carbon",
    "High_Clay":          "High clay",
    "channel_200m":       "Channel distance (200 m)",
    "channel_500m":       "Channel distance (500 m)",
    "channel_1000m":      "Channel distance (1000 m)",
    "effect_percent":     "Effectiveness (%)",
    "Intact":             "Intact",
}

def clean_predictor(name):
    return PRETTY_LABELS.get(name, name.replace("_", " ").title())

base = Path("../figures/paper1")
for stem in ["vegetation_response", "structural_integrity"]:
    src = base / f"SI_table_predictors_{stem}.csv"
    dst = base / f"SI_table_predictors_{stem}_clean.csv"
    df = pd.read_csv(src)
    df["predictor"] = df["predictor"].map(clean_predictor)
    df = df.drop(columns=[c for c in ["type", "n"] if c in df.columns])
    num_cols = df.select_dtypes(include="number").columns
    df[num_cols] = df[num_cols].round(3)
    df.to_csv(dst, index=False)
    print(f"Written: {dst}")
    print(df.head(3).to_string())
    print()
