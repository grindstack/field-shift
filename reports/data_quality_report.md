# Field Shift - Data Quality Report

Generated: 2026-11-15 20:09:52  |  Window: 2016-01 to 2025-12

## Overview

- Raw folder: `C:\Users\Hp\MyFolder\Field-Shift\data\raw`
- Datasets with NO file found: none
- Files ignored (no keyword match): none

## Assumptions

- File-to-dataset matching is done by keywords in the file name (see DATASETS in config.py).
- Column names are never hard-coded as required: dates and value columns are auto-detected and the result is printed and logged.
- NASA POWER -999 (and -9999 in any file) is treated as 'missing' and replaced with NaN.
- Monthly rainfall in NASA POWER columns whose name contains 'prec'/'rain' is SUMMED, all other daily columns are AVERAGED.
- A month with too few valid days (see MIN_VALID_DAY_FRACTION) is left as NaN, never filled or interpolated.
- If a monthly file has several rows per month (e.g. several points), they are AVERAGED per month and a warning is logged.
- Units are never silently converted. Only Kelvin->Celsius for MODIS LST is added (as a NEW column) when values clearly look like Kelvin.
- SoilGrids clay/sand/silt/nitrogen/phh2o/soc are stored as scaled integers. A derived column with the official ISRIC conversion factor (see SOILGRIDS_CONVERSIONS in config.py) is added; the raw column is kept.
- 'image_count' columns (IMERG/NDVI/LST) are observation counts (half-hourly granules or satellite scenes), not measurements - they get their own unit note instead of the dataset's measurement note.
- SRTM: if slope_max is far above slope_mean (see SLOPE_MAX_TO_MEAN_RATIO_FLAG), this is flagged as a likely localized outlier/artifact, not a value change.
- Missing months stay as empty cells (NaN) in the master table. Nothing is interpolated or invented.

## power  (daily)

- File: `nasa_power_sheikhupura_2016_2025.csv`
- Status: **ok**
- Rows raw -> after cleaning: 3653 -> 3653
- Exact duplicate rows removed: 0
- Rows sharing a date, merged: 0
- Missing-value codes replaced by NaN: none found
- Date detected from: columns 'year' + 'doy' (day of year)
- Date range: 2016-01-01 to 2025-12-31
- Expected periods in window: 3653, present: 3653, absent: 0

**Original -> standardized column names**

| original | standardized | raw dtype |
| --- | --- | --- |
| YEAR | year | int64 |
| DOY | doy | int64 |
| ALLSKY_SFC_SW_DWN | allsky_sfc_sw_dwn | float64 |
| T2M | t2m | float64 |
| T2M_MAX | t2m_max | float64 |
| T2M_MIN | t2m_min | float64 |
| RH2M | rh2m | float64 |
| WS2M | ws2m | float64 |
| PRECTOTCORR | prectotcorr | float64 |

**Missing values after cleaning**

| column | n_missing | pct_missing |
| --- | --- | --- |
| allsky_sfc_sw_dwn | 0 | 0 |
| t2m | 0 | 0 |
| t2m_max | 0 | 0 |
| t2m_min | 0 | 0 |
| rh2m | 0 | 0 |
| ws2m | 0 | 0 |
| prectotcorr | 0 | 0 |

**Unit / range checks (values never altered, except the noted extra column)**

| column | min | median | max | note |
| --- | --- | --- | --- | --- |
| allsky_sfc_sw_dwn | 1.16 | 17.38 | 29.66 | all values inside (0, 40) |
| t2m | 7.22 | 27.07 | 41.65 | all values inside (-50, 60) |
| t2m_max | 10.46 | 33.8 | 49.6 | all values inside (-50, 60) |
| t2m_min | -0.22 | 19.89 | 34.77 | all values inside (-50, 60) |
| rh2m | 8.47 | 44.78 | 95.12 | all values inside (0, 100) |
| ws2m | 0.48 | 1.41 | 5.19 | all values inside (0, 50) |
| prectotcorr | 0 | 0 | 87.23 | all values inside (0, 500) |

**Daily -> monthly rules**

| monthly column | rule |
| --- | --- |
| power_allsky_sfc_sw_dwn | mean |
| power_t2m | mean |
| power_t2m_max | mean |
| power_t2m_min | mean |
| power_rh2m | mean |
| power_ws2m | mean |
| power_prectotcorr | sum |

**Source file header (NASA POWER lists parameter units here)**

```
-BEGIN HEADER-
NASA/POWER Source Native Resolution Daily Data 
Dates (month/day/year): 01/01/2016 through 12/31/2025 in LST
Location: latitude  31.6746   longitude 73.9861 
elevation from MERRA-2: Average for 0.5 x 0.625 degree lat/lon region = 196.55 meters
The value for missing source data that cannot be computed or is outside of the sources availability range: -999 
parameter(s): 
ALLSKY_SFC_SW_DWN     CERES SYN1deg All Sky Surface Shortwave Downward Irradiance (MJ/m^2/day) 
T2M                   MERRA-2 Temperature at 2 Meters (C) 
T2M_MAX               MERRA-2 Temperature at 2 Meters Maximum (C) 
T2M_MIN               MERRA-2 Temperature at 2 Meters Minimum (C) 
RH2M                  MERRA-2 Relative Humidity at 2 Meters (%) 
WS2M                  MERRA-2 Wind Speed at 2 Meters (m/s) 
PRECTOTCORR           MERRA-2 Precipitation Corrected (mm/day) 
-END HEADER-
```

**Warnings**

_(none)_

## imerg  (monthly)

- File: `GPM_IMERG_Sheikhupura_Monthly_Rainfall_2016_2025.csv`
- Status: **ok**
- Rows raw -> after cleaning: 120 -> 120
- Exact duplicate rows removed: 0
- Rows sharing a date, merged: 0
- Missing-value codes replaced by NaN: none found
- Date detected from: columns 'year' + 'month' (day set to 1)
- Date range: 2016-01-01 to 2025-12-01
- Expected periods in window: 120, present: 120, absent: 0

**Original -> standardized column names**

| original | standardized | raw dtype |
| --- | --- | --- |
| date | date | object |
| year | year | int64 |
| month | month | int64 |
| rainfall_mm | rainfall_mm | float64 |
| image_count | image_count | int64 |

**Missing values after cleaning**

| column | n_missing | pct_missing |
| --- | --- | --- |
| imerg_rainfall_mm | 0 | 0 |
| imerg_image_count | 0 | 0 |

**Unit / range checks (values never altered, except the noted extra column)**

| column | min | median | max | note |
| --- | --- | --- | --- | --- |
| imerg_rainfall_mm | 0 | 29.44 | 303.6 | GUESS = accumulated mm per month. Unit unverified, NOT converted |
| imerg_image_count | 1344 | 1488 | 1488 | count of half-hourly IMERG granules combined into this month (GPM IMERG native temporal resolution is 30 min, so a full month = days_in_month * 48, e.g. 1488 for 31 days). This is an OBSERVATION COUNT, not a rainfall amount. |

**Warnings**

_(none)_

## ndvi  (monthly)

- File: `Landsat_NDVI_Sheikhupura_2016_2025.csv`
- Status: **ok**
- Rows raw -> after cleaning: 120 -> 120
- Exact duplicate rows removed: 0
- Rows sharing a date, merged: 0
- Missing-value codes replaced by NaN: none found
- Date detected from: columns 'year' + 'month' (day set to 1)
- Date range: 2016-01-01 to 2025-12-01
- Expected periods in window: 120, present: 120, absent: 0

**Original -> standardized column names**

| original | standardized | raw dtype |
| --- | --- | --- |
| date | date | object |
| year | year | int64 |
| month | month | int64 |
| mean_ndvi | mean_ndvi | float64 |
| image_count | image_count | int64 |

**Missing values after cleaning**

| column | n_missing | pct_missing |
| --- | --- | --- |
| ndvi_mean_ndvi | 0 | 0 |
| ndvi_image_count | 0 | 0 |

**Unit / range checks (values never altered, except the noted extra column)**

| column | min | median | max | note |
| --- | --- | --- | --- | --- |
| ndvi_mean_ndvi | 0.192 | 0.4337 | 0.6847 | values inside [-1, 1]: consistent with unscaled NDVI |
| ndvi_image_count | 3 | 8 | 16 | count of Landsat scenes (cloud-free overpasses) used to compute this month's mean NDVI. This is an OBSERVATION COUNT, not an NDVI value - no scale factor applies. |

**Warnings**

_(none)_

## lst  (monthly)

- File: `MODIS_LST_Sheikhupura_2016_2025.csv`
- Status: **ok**
- Rows raw -> after cleaning: 120 -> 120
- Exact duplicate rows removed: 0
- Rows sharing a date, merged: 0
- Missing-value codes replaced by NaN: none found
- Date detected from: columns 'year' + 'month' (day set to 1)
- Date range: 2016-01-01 to 2025-12-01
- Expected periods in window: 120, present: 120, absent: 0

**Original -> standardized column names**

| original | standardized | raw dtype |
| --- | --- | --- |
| date | date | object |
| year | year | int64 |
| month | month | int64 |
| mean_lst_c | mean_lst_c | float64 |
| image_count | image_count | int64 |

**Missing values after cleaning**

| column | n_missing | pct_missing |
| --- | --- | --- |
| lst_mean_lst_c | 0 | 0 |
| lst_image_count | 0 | 0 |

**Unit / range checks (values never altered, except the noted extra column)**

| column | min | median | max | note |
| --- | --- | --- | --- | --- |
| lst_mean_lst_c | 15.09 | 29.29 | 42.75 | median looks like degrees Celsius |
| lst_image_count | 3 | 4 | 4 | count of MODIS scenes used to compute this month's mean LST. This is an OBSERVATION COUNT, not a temperature value. |

**Warnings**

_(none)_

## soil  (static)

- File: `SoilGrids_Sheikhupura_Soil_Properties.csv`
- Status: **ok**
- Rows raw -> after cleaning: 1 -> 1
- Exact duplicate rows removed: 0
- Rows sharing a date, merged: n/a
- Missing-value codes replaced by NaN: none found

**Original -> standardized column names**

| original | standardized | raw dtype |
| --- | --- | --- |
| system:index | system_index | int64 |
| clay_0-5cm_mean | clay_0_5cm_mean | float64 |
| clay_5-15cm_mean | clay_5_15cm_mean | float64 |
| nitrogen_0-5cm_mean | nitrogen_0_5cm_mean | float64 |
| nitrogen_5-15cm_mean | nitrogen_5_15cm_mean | float64 |
| phh2o_0-5cm_mean | phh2o_0_5cm_mean | float64 |
| phh2o_5-15cm_mean | phh2o_5_15cm_mean | float64 |
| sand_0-5cm_mean | sand_0_5cm_mean | float64 |
| sand_5-15cm_mean | sand_5_15cm_mean | float64 |
| soc_0-5cm_mean | soc_0_5cm_mean | float64 |
| soc_5-15cm_mean | soc_5_15cm_mean | float64 |
| .geo | geo | object |

**Missing values after cleaning**

| column | n_missing | pct_missing |
| --- | --- | --- |
| system_index | 0 | 0 |
| clay_0_5cm_mean | 0 | 0 |
| clay_5_15cm_mean | 0 | 0 |
| nitrogen_0_5cm_mean | 0 | 0 |
| nitrogen_5_15cm_mean | 0 | 0 |
| phh2o_0_5cm_mean | 0 | 0 |
| phh2o_5_15cm_mean | 0 | 0 |
| sand_0_5cm_mean | 0 | 0 |
| sand_5_15cm_mean | 0 | 0 |
| soc_0_5cm_mean | 0 | 0 |
| soc_5_15cm_mean | 0 | 0 |
| geo | 0 | 0 |
| clay_0_5cm_mean_pct_derived | 0 | 0 |
| clay_5_15cm_mean_pct_derived | 0 | 0 |
| nitrogen_0_5cm_mean_g_per_kg_derived | 0 | 0 |
| nitrogen_5_15cm_mean_g_per_kg_derived | 0 | 0 |
| phh2o_0_5cm_mean_ph_derived | 0 | 0 |
| phh2o_5_15cm_mean_ph_derived | 0 | 0 |
| sand_0_5cm_mean_pct_derived | 0 | 0 |
| sand_5_15cm_mean_pct_derived | 0 | 0 |
| soc_0_5cm_mean_g_per_kg_derived | 0 | 0 |
| soc_5_15cm_mean_g_per_kg_derived | 0 | 0 |

**Unit / range checks (values never altered, except the noted extra column)**

| column | min | median | max | note |
| --- | --- | --- | --- | --- |
| clay_0_5cm_mean | 213.6 | 213.6 | 213.6 | SoilGrids mapped/scaled unit (ISRIC convention: raw = conventional x 10). Official conversion factor applied in NEW derived column 'clay_0_5cm_mean_pct_derived' = raw / 10 (conventional unit: pct); original column kept unchanged. |
| clay_5_15cm_mean | 230.4 | 230.4 | 230.4 | SoilGrids mapped/scaled unit (ISRIC convention: raw = conventional x 10). Official conversion factor applied in NEW derived column 'clay_5_15cm_mean_pct_derived' = raw / 10 (conventional unit: pct); original column kept unchanged. |
| nitrogen_0_5cm_mean | 1033 | 1033 | 1033 | SoilGrids mapped/scaled unit (ISRIC convention: raw = conventional x 100). Official conversion factor applied in NEW derived column 'nitrogen_0_5cm_mean_g_per_kg_derived' = raw / 100 (conventional unit: g_per_kg); original column kept unchanged. |
| nitrogen_5_15cm_mean | 752.8 | 752.8 | 752.8 | SoilGrids mapped/scaled unit (ISRIC convention: raw = conventional x 100). Official conversion factor applied in NEW derived column 'nitrogen_5_15cm_mean_g_per_kg_derived' = raw / 100 (conventional unit: g_per_kg); original column kept unchanged. |
| phh2o_0_5cm_mean | 81.71 | 81.71 | 81.71 | SoilGrids mapped/scaled unit (ISRIC convention: raw = conventional x 10). Official conversion factor applied in NEW derived column 'phh2o_0_5cm_mean_ph_derived' = raw / 10 (conventional unit: ph); original column kept unchanged. |
| phh2o_5_15cm_mean | 82.26 | 82.26 | 82.26 | SoilGrids mapped/scaled unit (ISRIC convention: raw = conventional x 10). Official conversion factor applied in NEW derived column 'phh2o_5_15cm_mean_ph_derived' = raw / 10 (conventional unit: ph); original column kept unchanged. |
| sand_0_5cm_mean | 314.9 | 314.9 | 314.9 | SoilGrids mapped/scaled unit (ISRIC convention: raw = conventional x 10). Official conversion factor applied in NEW derived column 'sand_0_5cm_mean_pct_derived' = raw / 10 (conventional unit: pct); original column kept unchanged. |
| sand_5_15cm_mean | 304.5 | 304.5 | 304.5 | SoilGrids mapped/scaled unit (ISRIC convention: raw = conventional x 10). Official conversion factor applied in NEW derived column 'sand_5_15cm_mean_pct_derived' = raw / 10 (conventional unit: pct); original column kept unchanged. |
| soc_0_5cm_mean | 111.8 | 111.8 | 111.8 | SoilGrids mapped/scaled unit (ISRIC convention: raw = conventional x 10). Official conversion factor applied in NEW derived column 'soc_0_5cm_mean_g_per_kg_derived' = raw / 10 (conventional unit: g_per_kg); original column kept unchanged. |
| soc_5_15cm_mean | 80.51 | 80.51 | 80.51 | SoilGrids mapped/scaled unit (ISRIC convention: raw = conventional x 10). Official conversion factor applied in NEW derived column 'soc_5_15cm_mean_g_per_kg_derived' = raw / 10 (conventional unit: g_per_kg); original column kept unchanged. |

**Warnings**

_(none)_

## srtm  (static)

- File: `SRTM_Terrain_Sheikhupura.csv`
- Status: **ok**
- Rows raw -> after cleaning: 1 -> 1
- Exact duplicate rows removed: 0
- Rows sharing a date, merged: n/a
- Missing-value codes replaced by NaN: none found

**Original -> standardized column names**

| original | standardized | raw dtype |
| --- | --- | --- |
| system:index | system_index | int64 |
| elevation_m_max | elevation_m_max | int64 |
| elevation_m_mean | elevation_m_mean | float64 |
| elevation_m_min | elevation_m_min | int64 |
| slope_degrees_max | slope_degrees_max | float64 |
| slope_degrees_mean | slope_degrees_mean | float64 |
| slope_degrees_min | slope_degrees_min | float64 |
| .geo | geo | object |

**Missing values after cleaning**

| column | n_missing | pct_missing |
| --- | --- | --- |
| system_index | 0 | 0 |
| elevation_m_max | 0 | 0 |
| elevation_m_mean | 0 | 0 |
| elevation_m_min | 0 | 0 |
| slope_degrees_max | 0 | 0 |
| slope_degrees_mean | 0 | 0 |
| slope_degrees_min | 0 | 0 |
| geo | 0 | 0 |

**Unit / range checks (values never altered, except the noted extra column)**

| column | min | median | max | note |
| --- | --- | --- | --- | --- |
| elevation_m_max | 258 | 258 | 258 | range looks plausible for metres (assumed). NOT converted |
| elevation_m_mean | 201.7 | 201.7 | 201.7 | range looks plausible for metres (assumed). NOT converted |
| elevation_m_min | 153 | 153 | 153 | range looks plausible for metres (assumed). NOT converted |
| slope_degrees_max | 48.54 | 48.54 | 48.54 | within 0-90: consistent with degrees. NOT converted |
| slope_degrees_mean | 2.122 | 2.122 | 2.122 | within 0-90: consistent with degrees. NOT converted |
| slope_degrees_min | 0 | 0 | 0 | within 0-90: consistent with degrees. NOT converted |

**Warnings**

- 'slope_degrees_max' (48.54 deg) is 22.9x 'slope_degrees_mean' (2.12 deg). Likely a small number of outlier pixels (canal embankments, built structures, roads, or SRTM void-fill/edge noise), not representative field slope. Suggested check: pull the slope histogram or p90/p95 percentile (not just min/mean/max) from the source, or inspect the slope raster for the pixel(s) driving the max, before using max slope in any model.

## Master monthly table

- Rows: 120 (expected 120)
- Data columns: 13
- Months where EVERY column has a value: 120

**Missing values per column**

| column | n_missing | pct_missing |
| --- | --- | --- |
| power_allsky_sfc_sw_dwn | 0 | 0 |
| power_t2m | 0 | 0 |
| power_t2m_max | 0 | 0 |
| power_t2m_min | 0 | 0 |
| power_rh2m | 0 | 0 |
| power_ws2m | 0 | 0 |
| power_prectotcorr | 0 | 0 |
| imerg_rainfall_mm | 0 | 0 |
| imerg_image_count | 0 | 0 |
| ndvi_mean_ndvi | 0 | 0 |
| ndvi_image_count | 0 | 0 |
| lst_mean_lst_c | 0 | 0 |
| lst_image_count | 0 | 0 |

**Per-source coverage**

| source | months_with_data | months_outside_window_dropped | months_all_empty |
| --- | --- | --- | --- |
| power | 120 | 0 | 0 |
| imerg | 120 | 0 | 0 |
| ndvi | 120 | 0 | 0 |
| lst | 120 | 0 | 0 |

**Static soil / terrain tables**

| source | rows | joined | explanation |
| --- | --- | --- | --- |
| soil | 1 | True | single row: joined as constant columns |
| srtm | 1 | True | single row: joined as constant columns |

**Basic statistics (master)**

| column | count | mean | std | min | 25% | 50% | 75% | max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| power_allsky_sfc_sw_dwn | 120 | 16.86 | 4.952 | 5.42 | 12.96 | 17.47 | 20.62 | 25.45 |
| power_t2m | 120 | 25.46 | 8.171 | 10.92 | 17.96 | 26.6 | 32.37 | 38.6 |
| power_t2m_max | 120 | 32.71 | 7.468 | 17.76 | 26.05 | 34.08 | 39.26 | 45.33 |
| power_t2m_min | 120 | 19.09 | 8.234 | 5.23 | 11.17 | 19.28 | 26.94 | 31.4 |
| power_rh2m | 120 | 45.9 | 14.69 | 20.89 | 35.68 | 45.42 | 54.22 | 81.27 |
| power_ws2m | 120 | 1.517 | 0.2849 | 1.007 | 1.321 | 1.497 | 1.703 | 2.203 |
| power_prectotcorr | 120 | 59.43 | 80.45 | 0 | 8.777 | 27.88 | 70.91 | 431.3 |
| imerg_rainfall_mm | 120 | 57.22 | 69.57 | 0 | 8.862 | 29.44 | 70.54 | 303.6 |
| imerg_image_count | 120 | 1461 | 38.76 | 1344 | 1440 | 1488 | 1488 | 1488 |
| ndvi_mean_ndvi | 120 | 0.442 | 0.1565 | 0.192 | 0.2965 | 0.4337 | 0.5991 | 0.6847 |
| ndvi_image_count | 120 | 9.05 | 3.63 | 3 | 6 | 8 | 12 | 16 |
| lst_mean_lst_c | 120 | 28.52 | 7.301 | 15.09 | 23.16 | 29.29 | 33.14 | 42.75 |
| lst_image_count | 120 | 3.833 | 0.3742 | 3 | 4 | 4 | 4 | 4 |

## What to verify manually

- Units of every column (especially IMERG, soil and LST) against the original data source documentation.
- Any WARNING listed above, especially multiple locations averaged per month.
- Whether the monthly rainfall rule (sum) matches the units in the NASA POWER header.
