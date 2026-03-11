# Data Dictionary — `merged.csv`

**Rows:** 775 (one per berm / structure)  
**Columns:** 105  
**Produced by:** `data processing - condition vegetation.ipynb` (final cell merges shapefile attributes)  
**Source datasets:** Google Earth Engine berm exports (`data/berm_exports/`), USDA SSURGO Soil Data Access API, `Berm_Directionality.shp`

---

## 1. Identifiers / System Fields

| Column | Type | Notes | Nulls |
|--------|------|-------|-------|
| `system:index` | string | Zero-padded integer sequence assigned by GEE export (e.g. `"00000000000000000000"`). Equivalent to `id`. | 0 |
| `id` | string | Same as `system:index`. | 0 |
| `.geo` | string (JSON) | Full GEE geometry export — LineString GeoJSON for each berm (primary GEE export). Used for display/mapping only. | 0 |
| `geo` | string (JSON) | Shapefile-sourced LineString GeoJSON (from `Berm_Directionality.shp`). Truncated column name from DBF. nulls = 25 where no shapefile match was found. | 25 |
| `AOI` | string | Area of Interest identifier (`AOI1`–`AOI5`). Divides the Altar Valley study area into five spatial sub-units. | 25 |

---

## 2. Structure Attributes (from GEE field survey exports)

| Column | Type | Values / Range | Notes | Nulls |
|--------|------|---------------|-------|-------|
| `Type` | string | `Berm`, `Check dam`, `Concrete Structure`, `Rock Gabion Structure`, `Spur` | Structure type. Primary analyses use `Type == 'Berm'` only. | 0 |
| `Note` | string | `MLC`, `MLC;042919`, `MLC;050819`, `MLC;110222`, `TCD` | Observer / survey-date codes recorded in field. | 0 |
| `Notes` | string | `Rockgabion`, `Watercontrol` | Supplementary field notes. Populated only for non-berm structures. | 743 |
| `Structure_` | string | `Rockgabion`, `Watercontrol` | Duplicate of `Notes`; from a second survey CSV. | 743 |
| `Shape_Leng` | float (m) | 4.6–521.2 | Berm plan-view length in metres derived from GEE geometry. | 0 |
| `compare` | int | 0, 1 | Flag column; 1 = berm matched between two survey rounds. Exact usage recorded in field protocol. | 0 |

---

## 3. Location

| Column | Type | Values / Range | Notes | Nulls |
|--------|------|---------------|-------|-------|
| `latitude` | float (°N) | 31.48–32.07 | Berm centroid latitude (WGS 84). | 0 |
| `longitude` | float (°W) | −111.60 – −111.23 | Berm centroid longitude (WGS 84). | 0 |
| `landform` | int | 0, 1 | Coarse proximity classification from an original field-survey column; 0 = Upland, 1 = Flood plain. Superseded by `Landform` (SSURGO-derived). See also `proximity`. | 0 |
| `AREASYMBOL` | string | `AZ667`, `AZ669` | USDA SSURGO soil survey area symbols for the two soil survey areas covering the study region. | 0 |
| `MUSYM` | string | e.g. `1`, `12`, `17` … | Map-unit symbol within the soil survey — human-readable soil unit code. | 0 |

---

## 4. Soil / SSURGO Attributes (from Soil Data Access API)

These columns are keyed via `MUKEY` → lookup dictionaries built in the data-processing notebook.

| Column | Type | Values / Range | Notes | Nulls |
|--------|------|---------------|-------|-------|
| `MUKEY` | int | 53738–1 423 101 | USDA SSURGO map-unit key. Primary join key between GEE data and SDA attributes. | 0 |
| `MapUnitName` | string | e.g. `Glendale silt loam, 0 to 3 percent slopes` | Full SSURGO map-unit name including slope range. Populated for the original 9 curated MUKEYs only; nulls for extended MUKEYs. | 131 |
| `SlopeClass` | string | `low`, `high` | Coarse curated slope class from the original MUKEY dictionary. `low` ≤ ~3 %, `high` > ~3 %. | 131 |
| `Landform` | string | `Fan terraces`, `Flood plains`, `Stream terraces` | Landform class derived by `classify_landform()` from SSURGO `geomfname` field. Used as the primary landform predictor in all analyses. | 0 |
| `Landform_1` | string | raw SSURGO landform names (e.g. `Fan terraces, hills`, `Alluvial fans`) | Unclassified (raw) SSURGO landform from the shapefile merge. Useful for cross-checking `Landform`. Truncated shapefile column name. | 25 |
| `GroupedLan` | string | `Fan terraces`, `Flood plains`, `Stream terraces` | Alternative grouped landform from the shapefile (may differ from `Landform` for edge-case MUKEYs). | 25 |
| `ParentMaterial` | string | e.g. `Mixed alluvium`, `Alluvium derived from granite …` | SSURGO parent-material description for the dominant soil component. Populated for original curated MUKEYs only. | 131 |
| `ParentMate` | string | same as above | Truncated (≤10 char) shapefile version of parent material — from extended MUKEY lookup via SDA. | 25 |
| `GroupedPar` | string | `Mixed alluvium`, `Moderately fine and/or moderately coarse textured alluvium`, `In situ bedrock-derived alluvium and/or colluvium and/or residuum` | Grouped parent-material category from the shapefile. | 25 |
| `TypicalProfile` | string | e.g. `A-C`, `A-Bt-2Bt-3BCt` | Horizon sequence string(s) for major soil components, auto-built from SDA horizon query. Multiple profiles per MUKEY are comma-separated. | 0 |
| `TypicalPro` | string | same as above | Truncated shapefile version of `TypicalProfile` (≤10 chars DBF limit). | 25 |
| `Texture` | string | `Clay loam`, `Fine sandy loam`, `Loam`, `Loamy coarse sand`, `Loamy sand`, `Sandy clay loam`, `Sandy loam`, `Silt loam` | Surface-horizon texture class from SDA (`texcl` field). | 0 |
| `claytotal_r` | float (%) | 4.0–32.5 | Surface-horizon clay content (representative value) from SDA. | 0 |
| `sandtotal_r` | float (%) | 11.4–83.5 | Surface-horizon sand content (representative value) from SDA. | 0 |
| `silttotal_r` | float (%) | 9.0–68.6 | Surface-horizon silt content (representative value) from SDA. | 0 |
| `Soil_Development` | string | `B horizon`, `No B horizon` | Derived from `TypicalProfile`; `B horizon` if any horizon name contains 'B'. Proxy for pedogenic development. | 0 |
| `GroupedSoi` | string | `Bt and/or Bk horizon`, `No Bt and/or Bk horizon` | More specific grouping of soil development from the shapefile (distinguishes argillic/calcic B horizons). | 25 |
| `High_Clay` | bool | True/False | True if `claytotal_r` > median clay content across all berms. | 0 |
| `MapUnitNam` | string | same as `MapUnitName` | Truncated version from shapefile merge (≤10 char). | 25 |

---

## 5. Berm Failure / Structural Condition

| Column | Type | Values / Range | Notes | Nulls |
|--------|------|---------------|-------|-------|
| `Fail_Type` | string | `Intact`, `Breach`, `Flank` | Primary structural-integrity outcome. `Breach` = perpendicular failure through the berm; `Flank` = lateral scour around the berm end. Rows with `Breach and Flank` are removed in the data-processing notebook. | 0 |
| `Condition` | string | `Intact`, `Degraded` | Binary collapse of `Fail_Type`: `Intact` as-is; all other types → `Degraded`. | 0 |
| `Intact` | bool | True/False | True if `Condition == 'Intact'`. Convenience boolean for analysis. | 0 |

---

## 6. Vegetation Response (SAVI)

SAVI = Soil-Adjusted Vegetation Index. Subscripts: `U` = upslope of berm, `D` = downslope; `_60` = 60 m buffer; `background` = reference SAVI measured away from the berm.

| Column | Type | Values / Range | Notes | Nulls |
|--------|------|---------------|-------|-------|
| `saviU_60` | float | 0.072–0.371 | Mean SAVI in a 60 m upslope buffer. | 0 |
| `saviD_60` | float | 0.060–0.378 | Mean SAVI in a 60 m downslope buffer. | 0 |
| `savi_background` | float | 0.078–0.202 | Reference SAVI measured at a background (away-from-berm) location. Zero values replaced with NaN in processing. | 0 |
| `effect` | float | −1.16–1.75 | Normalised vegetation response: `(saviU_60 − saviD_60) / savi_background`. | 0 |
| `effect_percent` | float (%) | −116.1–174.6 | `effect × 100`. Positive = more vegetation upslope (berm trapping runoff/sediment). | 0 |
| `effective` | bool | True/False | True if `effect_percent > 7`. Threshold of 7 % used as the minimum detectable vegetation response. | 0 |
| `Effective` | string | `Vegetation response`, `No vegetation response` | Labelled version of `effective` using canonical labels from `src/constants.py` (`LBL_EFFECTIVE` / `LBL_INEFFECTIVE`). | 0 |
| `savi_backg` | float | 0.082–0.195 | Truncated shapefile version of `savi_background` from the second GEE export. 25 nulls where no shapefile row matched. | 25 |
| `effect_per` | float (%) | −112.8–161.7 | Truncated shapefile version of `effect_percent`. | 25 |

---

## 7. Topography (from GEE 30 m DEM)

Buffer suffixes: `U` = upslope, `D` = downslope, `_60` = 60 m radius, `_100` = 100 m, `_200` = 200 m.

| Column | Type | Values / Range | Notes | Nulls |
|--------|------|---------------|-------|-------|
| `slope_100` | float (%) | 0.005–13.0 | Mean slope in a 100 m upslope buffer. Used as the primary slope predictor. | 0 |
| `slope_200` | float (%) | 0.005–13.4 | Mean slope in a 200 m upslope buffer. | 0 |
| `slopeU_60` | float (%) | −8.5–8.7 | Mean slope in 60 m upslope buffer (signed; negative = concave). | 0 |
| `slopeD_60` | float (%) | −5.0–7.9 | Mean slope in 60 m downslope buffer. | 0 |
| `slopeU_100` | float (%) | 0.005–13.0 | Mean slope in 100 m upslope buffer (absolute). | 0 |
| `slopeD_100` | float (%) | −13.0 – −0.005 | Downslope slope (negative = descending away from berm). | 0 |
| `slopeU_200` | float (%) | 0.005–13.4 | Mean slope in 200 m upslope buffer. | 0 |
| `slopeD_200` | float (%) | −13.4 – −0.005 | Mean slope 200 m downslope. | 0 |
| `berm_angle` | float (°) | −89.8–90.0 | Signed angle of berm relative to flow direction. 0° = perpendicular; ±90° = parallel. | 0 |
| `berm_elev` | float (m) | 787.3–1191.5 | Elevation of the berm centroid (m a.s.l.). | 67 |
| `zU_60` | float (m) | 781.7–1197.2 | Mean elevation of 60 m upslope buffer. | 0 |
| `zD_60` | float (m) | 781.2–1193.4 | Mean elevation of 60 m downslope buffer. | 0 |
| `aspectU_60` | float (°) | −180–167 | Mean aspect of 60 m upslope buffer (−180 to 180 °; −1 = flat). | 0 |
| `aspectD_60` | float (°) | −180–157 | Mean aspect of 60 m downslope buffer. | 0 |
| `convU_60` | float | −13.0–7.9 | Mean terrain convergence index in 60 m upslope buffer. Negative = divergent (ridges), positive = convergent (valleys). | 0 |
| `convD_60` | float | −5.3–14.0 | Mean terrain convergence index in 60 m downslope buffer. | 0 |
| `FA_30_max` | float (cells) | 11–17 372 300 | Maximum flow-accumulation value (30 m grid) within a buffer. Large values indicate position on major drainage paths. | 0 |
| `FA_30_mean` | float (cells) | 1.2–1 110 507 | Mean flow accumulation (30 m grid). | 0 |
| `FA_60_max` | float (cells) | 19–20 192 066 | Maximum flow accumulation (60 m grid). | 0 |
| `FA_60_mean` | float (cells) | 3.4–1 147 889 | Mean flow accumulation (60 m grid). | 0 |
| `Slope_Class` | string | `Shallow (≤ 2%)`, `Steep (> 2%)` | Binary classification of `slope_100`. Threshold of 2 % chosen to separate low-gradient flood-plain/terrace berms from steeper fan berms. | 0 |
| `Slope_Clas` | string | same | Truncated shapefile version. | 25 |

---

## 8. Proximity Metrics

| Column | Type | Values / Range | Notes | Nulls |
|--------|------|---------------|-------|-------|
| `other_dist` | float (m) | 3.7–42 731 | Distance to the nearest other structure (berm or check dam). | 0 |
| `other_elev` | float (m) | 781.6–1195.9 | Elevation of the nearest other structure. | 0 |
| `road_dist` | float (m) | 0–1911 | Distance to the nearest road. Zero values may indicate berm is on a road boundary. | 0 |
| `channel_10m` | float (fraction) | 0–0.087 | Fraction of 10 m radius buffer classified as a channel. | 0 |
| `channel_100m` | float (fraction) | 0–0.714 | Fraction of 100 m buffer classified as channel. | 0 |
| `channel_200m` | float (fraction) | 0–0.999 | Fraction of 200 m buffer classified as channel. | 0 |
| `channel_500m` | float (fraction) | 0–1.0 | Fraction of 500 m buffer. | 0 |
| `channel_700m` | float (fraction) | 0–1.0 | Fraction of 700 m buffer. | 0 |
| `channel_1000m` | float (fraction) | 0–1.0 | Fraction of 1000 m buffer classified as channel. | 0 |
| `proximity` | string | `Upland`, `Flood plain` | Derived from the integer `landform` field (0 = Upland, 1 = Flood plain). Coarse proximity label. | 0 |

---

## 9. Surface Soil (Remote-Sensing Proxies, from GEE)

These columns estimate surface soil properties from remote sensing within upslope / downslope buffers, providing spatially continuous alternatives to point SSURGO values. Many have truncated shapefile equivalents (25 nulls each from the shapefile merge).

| Column | Shapefile twin | Type | Values / Range | Notes |
|--------|---------------|------|---------------|-------|
| `surf_clayU_60` | `surfclayU_` | float (%) | 16.2–32.0 | Estimated surface clay % in 60 m upslope buffer. |
| `surf_clayD_60` | `surfclayD_` | float (%) | 17.0–32.0 | Estimated surface clay % in 60 m downslope buffer. |
| `surf_clay_background` | `surfclay_b` | float (%) | 18.4–29.5 | Background surface clay % (reference location). |
| `surf_claybg` | `surfclaybg` | float (%) | 0–32.0 | Alternative background clay estimate; 0 may indicate masked pixel. 1 null in primary, 25 in shapefile. |
| `surf_sandU_60` | `surfsandU_` | float (%) | 39.0–62.8 | Estimated surface sand % in 60 m upslope buffer. |
| `surf_sandD_60` | `surfsandD_` | float (%) | 42.0–61.0 | Estimated surface sand % in 60 m downslope buffer. |
| `surf_sand_background` | `surfsand_b` | float (%) | 43.9–61.9 | Background surface sand %. |
| `surf_sandbg` | `surfsandbg` | float (%) | 0–61.4 | Alternative background sand estimate. 1 null in primary, 25 in shapefile. |
| `surfsocU_60` | `surfsocU_6` | float | 1.0–3.0 | Surface soil organic-carbon proxy in 60 m upslope buffer (ordinal index 1–3). |
| `surfsocD_60` | `surfsocD_6` | float | 1.0–3.0 | Surface SOC proxy in 60 m downslope buffer. |
| `surfsoc_background` | `surfsoc_ba` | float | 1.0–2.55 | Background SOC proxy. |
| `surfsocbg` | *(same)* | float | 1.0–3.0 | Alternative background SOC estimate. 1 null in primary. |

---

## 10. Derived / Classified Variables

| Column | Type | Values / Range | Notes | Nulls |
|--------|------|---------------|-------|-------|
| `Berm_Length_Class` | string | `Short (≤ 50 m)`, `Long (> 50 m)` | Binary length class; threshold of 50 m from literature (Nichols et al., 2023). | 0 |
| `Berm_Lengt` | string | same | Truncated shapefile version. | 25 |
| `Direction` | string | `parallel`, `perpendicular`, `undetermined` | Berm orientation relative to drainage flow direction, from `Berm_Directionality.shp`. `perpendicular` berms intercept overland flow directly; `parallel` berms route it laterally. | 25 |

---

## 11. Columns Not Used in Primary Analyses

The following columns are retained for completeness but are not directly used as predictors or outcomes in the manuscripts.

| Column | Reason |
|--------|--------|
| `system:index`, `id` | System identifiers; no analytical value. |
| `.geo`, `geo` | Raw GeoJSON geometry strings. |
| `Note`, `Notes`, `Structure_` | Field notes; sparse / not standardised. |
| `compare` | Internal matching flag. |
| `MUSYM`, `AREASYMBOL` | Soil survey administrative codes. |
| `landform` (int 0/1) | Raw integer; superseded by `Landform`. |
| `proximity` | Coarser version of `Landform`. |
| `MapUnitName`, `MapUnitNam`, `SlopeClass`, `ParentMaterial`, `ParentMate` | Available only for 9 original curated MUKEYs (131 nulls); superseded by full SDA lookup. |
| `effect_per`, `MapUnitNam`, `Landform_1`, `TypicalPro`, `GroupedLan`, `GroupedPar`, `GroupedSoi`, `Berm_Lengt`, `Slope_Clas`, `savi_backg`, `surfclayU_`, `surfsandD_`, etc. | Truncated shapefile-merge duplicates (25 nulls). Use the non-truncated primary columns instead. |

---

## Notes on Column Truncation

Column names from DBF-format shapefiles are limited to **10 characters**. When the `Berm_Directionality.shp` was merged in, several columns were added with truncated names. In each case the non-truncated GEE-export column should be preferred. The truncated columns can be identified by their 25-null count (the number of rows with no shapefile match).

---

*Last updated: 2026-03-10. Regenerate by running the final cells of `data processing - condition vegetation.ipynb`.*
