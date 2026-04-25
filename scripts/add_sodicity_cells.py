"""Insert sodicity-related cells into notebook 1, and update cell 10 mappings.

Idempotent: re-running replaces the inserted cells (matched by leading marker).
"""
import json
from pathlib import Path

NB_PATH = Path("notebooks/1 data processing - condition vegetation.ipynb")

CHEM_MARKER = "# --- Fetch chemistry (SAR / sodicity) from SDA ---"
TAX_MARKER = "# --- Fetch component taxonomy (sodic / smectitic / vertic flags) from SDA ---"
SUMMARY_MARKER = "# --- Sodicity summary for manuscript caveat ---"

CHEM_SRC = '''\
# --- Fetch chemistry (SAR / sodicity) from SDA ---
# For the dominant component of each MUKEY, retrieve all horizons with
# sar_r (Sodium Adsorption Ratio), ec_r, ph1to1h2o_r, cec7_r.
# Build per-MUKEY summaries:
#   SAR_surface       -- sar_r of topmost horizon
#   SAR_max_upper1m   -- max sar_r across horizons with hzdept_r < 100 cm
#   Sodic_surface     -- SAR_surface > 13 (classical sodic threshold)
#   Sodic_subsurface  -- SAR_max_upper1m > 13

def fetch_chemistry_batch(batch_mukeys):
    in_list = ",".join(f"'{m}'" for m in batch_mukeys)
    sql = f"""
    WITH dom AS (
      SELECT
        c.mukey, c.cokey, c.compname, c.comppct_r,
        ROW_NUMBER() OVER (PARTITION BY c.mukey ORDER BY c.comppct_r DESC) AS rn
      FROM component c
      WHERE c.mukey IN ({in_list})
    )
    SELECT
      d.mukey,
      ch.cokey,
      ch.chkey,
      ch.hzname,
      ch.hzdept_r,
      ch.hzdepb_r,
      ch.sar_r,
      ch.ec_r,
      ch.ph1to1h2o_r,
      ch.cec7_r
    FROM dom d
    JOIN chorizon ch ON ch.cokey = d.cokey
    WHERE d.rn = 1
      AND ch.hzdept_r IS NOT NULL
      AND ch.hzdepb_r IS NOT NULL
    ORDER BY d.mukey, ch.hzdept_r;
    """
    resp = sda_post(sql)
    dfb = sda_to_df(resp).rename(columns={
        0: "mukey", 1: "cokey", 2: "chkey", 3: "hzname",
        4: "hzdept_r", 5: "hzdepb_r",
        6: "sar_r", 7: "ec_r", 8: "ph1to1h2o_r", 9: "cec7_r",
    })
    if dfb.empty:
        return dfb
    dfb["mukey"] = dfb["mukey"].astype(str)
    for col in ["hzdept_r", "hzdepb_r", "sar_r", "ec_r", "ph1to1h2o_r", "cec7_r"]:
        dfb[col] = pd.to_numeric(dfb[col], errors="coerce")
    return dfb

BATCH_SIZE = 150
_chem_parts = []
for i in range(0, len(mukeys), BATCH_SIZE):
    _chem_parts.append(fetch_chemistry_batch(mukeys[i:i + BATCH_SIZE]))
df_chem = pd.concat(_chem_parts, ignore_index=True)

# Per-MUKEY sodicity summaries (dominant component, all horizons).
SODIC_THRESHOLD = 13.0
UPPER_M_CM = 100.0

def _sar_surface(g):
    g = g.dropna(subset=["sar_r", "hzdept_r"]).sort_values("hzdept_r")
    return float(g["sar_r"].iloc[0]) if not g.empty else float("nan")

def _sar_max_upper1m(g):
    g = g.dropna(subset=["sar_r", "hzdept_r"])
    g = g[g["hzdept_r"] < UPPER_M_CM]
    return float(g["sar_r"].max()) if not g.empty else float("nan")

_sar_surface_by_mukey = df_chem.groupby("mukey").apply(_sar_surface)
_sar_max_by_mukey     = df_chem.groupby("mukey").apply(_sar_max_upper1m)
_n_horizons_by_mukey  = df_chem.dropna(subset=["sar_r"]).groupby("mukey")["sar_r"].size()

MUKEY_to_SAR_surface     = _sar_surface_by_mukey.to_dict()
MUKEY_to_SAR_max_upper1m = _sar_max_by_mukey.to_dict()
MUKEY_to_SAR_n_horizons  = _n_horizons_by_mukey.to_dict()

print(f"MUKEYs with any SAR data: "
      f"{sum(pd.notna(v) for v in MUKEY_to_SAR_surface.values())} / {len(mukeys)}")
print(f"MUKEYs with SAR_surface > {SODIC_THRESHOLD}: "
      f"{sum((not pd.isna(v)) and v > SODIC_THRESHOLD for v in MUKEY_to_SAR_surface.values())}")
print(f"MUKEYs with SAR_max_upper1m > {SODIC_THRESHOLD}: "
      f"{sum((not pd.isna(v)) and v > SODIC_THRESHOLD for v in MUKEY_to_SAR_max_upper1m.values())}")
'''

TAX_SRC = '''\
# --- Fetch component taxonomy (sodic / smectitic / vertic flags) from SDA ---
# For the dominant component, pull taxclname (full family-level taxonomy string)
# plus subgroup / great group / order. Then derive boolean flags by regex.

def fetch_taxonomy_batch(batch_mukeys):
    in_list = ",".join(f"'{m}'" for m in batch_mukeys)
    sql = f"""
    WITH dom AS (
      SELECT
        c.mukey, c.cokey, c.compname, c.comppct_r,
        c.taxclname, c.taxsubgrp, c.taxgrtgroup, c.taxorder,
        ROW_NUMBER() OVER (PARTITION BY c.mukey ORDER BY c.comppct_r DESC) AS rn
      FROM component c
      WHERE c.mukey IN ({in_list})
    )
    SELECT mukey, compname, comppct_r, taxclname, taxsubgrp, taxgrtgroup, taxorder
    FROM dom
    WHERE rn = 1
    ORDER BY mukey;
    """
    resp = sda_post(sql)
    dfb = sda_to_df(resp).rename(columns={
        0: "mukey", 1: "compname", 2: "comppct_r",
        3: "taxclname", 4: "taxsubgrp", 5: "taxgrtgroup", 6: "taxorder",
    })
    if dfb.empty:
        return dfb
    dfb["mukey"] = dfb["mukey"].astype(str)
    return dfb

_tax_parts = []
for i in range(0, len(mukeys), BATCH_SIZE):
    _tax_parts.append(fetch_taxonomy_batch(mukeys[i:i + BATCH_SIZE]))
df_tax = pd.concat(_tax_parts, ignore_index=True)

# Concatenate taxonomy fields into one searchable string per MUKEY for regex flagging.
def _flag_from_row(row):
    parts = [str(row.get(c, "") or "") for c in ("taxclname", "taxsubgrp", "taxgrtgroup", "taxorder")]
    s = " ".join(parts)
    s_lower = s.lower()
    return {
        "Tax_class":          row.get("taxclname"),
        "Tax_sodic_subgroup": bool(re.search(r"\\bsodic\\b", s_lower)),
        "Tax_natric":         bool(re.search(r"\\bnatr", s_lower)),
        "Tax_smectitic":      bool(re.search(r"\\bsmectitic\\b", s_lower)),
        "Tax_vertic":         bool(re.search(r"vert(ic|i)", s_lower)),
    }

df_tax_flags = pd.DataFrame([_flag_from_row(r) for _, r in df_tax.iterrows()])
df_tax_flags["mukey"] = df_tax["mukey"].values

MUKEY_to_taxclass        = df_tax_flags.set_index("mukey")["Tax_class"].to_dict()
MUKEY_to_tax_sodic       = df_tax_flags.set_index("mukey")["Tax_sodic_subgroup"].to_dict()
MUKEY_to_tax_natric      = df_tax_flags.set_index("mukey")["Tax_natric"].to_dict()
MUKEY_to_tax_smectitic   = df_tax_flags.set_index("mukey")["Tax_smectitic"].to_dict()
MUKEY_to_tax_vertic      = df_tax_flags.set_index("mukey")["Tax_vertic"].to_dict()

print("Taxonomic flag counts across MUKEYs:")
print(f"  Sodic subgroup : {sum(MUKEY_to_tax_sodic.values())}")
print(f"  Natric         : {sum(MUKEY_to_tax_natric.values())}")
print(f"  Smectitic      : {sum(MUKEY_to_tax_smectitic.values())}")
print(f"  Vertic         : {sum(MUKEY_to_tax_vertic.values())}")
'''

SUMMARY_SRC = '''\
# --- Sodicity summary for manuscript caveat ---
# Coverage and threshold-exceedance stats over berm rows (post-merge).
# Use whichever DataFrame holds the merged berm-level data.
_df_for_summary = merged if "merged" in globals() else data
_n = len(_df_for_summary)
print(f"Total berm rows: {_n}")

_sar_s  = pd.to_numeric(_df_for_summary.get("SAR_surface"),     errors="coerce")
_sar_mx = pd.to_numeric(_df_for_summary.get("SAR_max_upper1m"), errors="coerce")
print(f"\\nSAR coverage (non-null):")
print(f"  SAR_surface     : {_sar_s.notna().sum():4d} / {_n}  ({100*_sar_s.notna().mean():.1f}%)")
print(f"  SAR_max_upper1m : {_sar_mx.notna().sum():4d} / {_n}  ({100*_sar_mx.notna().mean():.1f}%)")

if _sar_s.notna().any():
    print(f"\\nSAR_surface > 13 (sodic threshold):")
    _flag = _sar_s > 13
    print(f"  Sites exceeding: {int(_flag.sum()):4d} / {int(_sar_s.notna().sum())} "
          f"with data ({100*_flag.sum()/max(_sar_s.notna().sum(),1):.1f}%)")
if _sar_mx.notna().any():
    print(f"\\nSAR_max_upper1m > 13 (any horizon in upper 1 m):")
    _flag = _sar_mx > 13
    print(f"  Sites exceeding: {int(_flag.sum()):4d} / {int(_sar_mx.notna().sum())} "
          f"with data ({100*_flag.sum()/max(_sar_mx.notna().sum(),1):.1f}%)")
    print(f"\\nSAR_max_upper1m percentiles (across berms with data):")
    print(_sar_mx.dropna().quantile([0.05, 0.25, 0.50, 0.75, 0.95]).round(2).to_string())

print("\\nTaxonomic flags across berm sites:")
for col in ["Tax_sodic_subgroup", "Tax_natric", "Tax_smectitic", "Tax_vertic"]:
    if col in _df_for_summary.columns:
        n_true = int(_df_for_summary[col].fillna(False).astype(bool).sum())
        print(f"  {col:22s}: {n_true:4d} / {_n}  ({100*n_true/_n:.1f}%)")

# Crosstabs: taxonomic flags by Landform and Fail_Type
for flag in ["Tax_smectitic", "Tax_vertic", "Tax_sodic_subgroup", "Tax_natric"]:
    if flag in _df_for_summary.columns and "Landform" in _df_for_summary.columns:
        ct = pd.crosstab(_df_for_summary["Landform"],
                         _df_for_summary[flag].fillna(False).astype(bool),
                         margins=True)
        if ct.shape[1] > 1:
            print(f"\\n{flag} by Landform:")
            print(ct.to_string())

if "Fail_Type" in _df_for_summary.columns:
    for flag in ["Tax_smectitic", "Tax_vertic"]:
        if flag in _df_for_summary.columns:
            ct = pd.crosstab(_df_for_summary["Fail_Type"],
                             _df_for_summary[flag].fillna(False).astype(bool),
                             margins=True)
            if ct.shape[1] > 1:
                print(f"\\n{flag} by Fail_Type:")
                print(ct.to_string())
'''


def make_cell(cell_id, src):
    return {
        "cell_type": "code",
        "id": cell_id,
        "metadata": {"language": "python"},
        "source": src.splitlines(keepends=True),
        "outputs": [],
        "execution_count": None,
    }


def remove_marker_cells(cells, markers):
    return [
        c for c in cells
        if not (c.get("cell_type") == "code"
                and any("".join(c.get("source", [])).lstrip().startswith(m) for m in markers))
    ]


def find_cell_idx_by_starts(cells, prefix):
    for i, c in enumerate(cells):
        if c.get("cell_type") == "code" and "".join(c.get("source", [])).lstrip().startswith(prefix):
            return i
    return -1


def main():
    nb = json.loads(NB_PATH.read_text())
    cells = nb["cells"]

    # Idempotent: drop any previously-inserted cells.
    cells = remove_marker_cells(cells, [CHEM_MARKER, TAX_MARKER, SUMMARY_MARKER])

    # Insert chem & taxonomy cells right after the soil-depth-fetch cell.
    depth_idx = find_cell_idx_by_starts(cells, "# --- Fetch soil depth")
    assert depth_idx >= 0, "soil-depth fetch cell not found"
    insert_at = depth_idx + 1
    cells.insert(insert_at, make_cell("sodic-chem-fetch", CHEM_SRC))
    cells.insert(insert_at + 1, make_cell("sodic-tax-fetch", TAX_SRC))

    # Patch the mapping cell (cell starting with "# Rebuild MUKEY") to add new
    # data[...] = data['MUKEY'].map(...) lines.
    map_idx = find_cell_idx_by_starts(cells, "# Rebuild MUKEY -> typical horizon")
    assert map_idx >= 0, "mapping cell not found"
    map_cell = cells[map_idx]
    map_src = "".join(map_cell["source"])
    SODIC_BLOCK = (
        "\n"
        "# Sodicity / chemistry & taxonomy lookups\n"
        "data['SAR_surface']        = data['MUKEY'].map(MUKEY_to_SAR_surface)\n"
        "data['SAR_max_upper1m']    = data['MUKEY'].map(MUKEY_to_SAR_max_upper1m)\n"
        "data['SAR_n_horizons']     = data['MUKEY'].map(MUKEY_to_SAR_n_horizons)\n"
        "data['Sodic_surface']      = data['SAR_surface']     > 13\n"
        "data['Sodic_subsurface']   = data['SAR_max_upper1m'] > 13\n"
        "data['Tax_class']          = data['MUKEY'].map(MUKEY_to_taxclass)\n"
        "data['Tax_sodic_subgroup'] = data['MUKEY'].map(MUKEY_to_tax_sodic)\n"
        "data['Tax_natric']         = data['MUKEY'].map(MUKEY_to_tax_natric)\n"
        "data['Tax_smectitic']      = data['MUKEY'].map(MUKEY_to_tax_smectitic)\n"
        "data['Tax_vertic']         = data['MUKEY'].map(MUKEY_to_tax_vertic)\n"
    )
    if "MUKEY_to_SAR_surface" not in map_src:
        anchor = "data['restriction_depth_cm'] = data['MUKEY'].map(MUKEY_to_restriction_depth)\n"
        assert anchor in map_src, "anchor line for sodicity insertion not found in mapping cell"
        map_src = map_src.replace(anchor, anchor + SODIC_BLOCK, 1)
        map_cell["source"] = map_src.splitlines(keepends=True)

    # Append summary cell at end.
    cells.append(make_cell("sodic-summary", SUMMARY_SRC))

    nb["cells"] = cells
    NB_PATH.write_text(json.dumps(nb, indent=1) + "\n")
    print(f"OK: rewrote {NB_PATH}")


if __name__ == "__main__":
    main()
