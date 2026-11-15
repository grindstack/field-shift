"""
config.py - ALL settings for the Field Shift preprocessing pipeline.

If your CSV files or columns look different from what the scripts expect,
this is the only file you should need to edit.
"""
from pathlib import Path

# ----------------------------------------------------------------------------
# Folders (relative to the Field-Shift project folder)
# ----------------------------------------------------------------------------
PROJECT_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_DIR / "data" / "raw"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
REPORT_DIR = PROJECT_DIR / "reports"
FIGURE_DIR = REPORT_DIR / "figures"

# ----------------------------------------------------------------------------
# Study window (monthly master table covers exactly these months)
# ----------------------------------------------------------------------------
START_MONTH = "2016-01"
END_MONTH = "2025-12"

# ----------------------------------------------------------------------------
# ASSUMPTION: which raw CSV belongs to which dataset is decided by keywords in
# the FILE NAME (case-insensitive). The first dataset (top to bottom) whose
# keyword appears in a file name gets that file.
# "kind" = daily | monthly | static
# ----------------------------------------------------------------------------
DATASETS = {
    "power": {"kind": "daily",   "keywords": ["power"]},
    "imerg": {"kind": "monthly", "keywords": ["imerg", "gpm", "rainfall", "precip"]},
    "ndvi":  {"kind": "monthly", "keywords": ["ndvi", "landsat"]},
    "lst":   {"kind": "monthly", "keywords": ["lst", "modis", "land_surface", "surface_temp"]},
    "soil":  {"kind": "static",  "keywords": ["soil"]},
    "srtm":  {"kind": "static",  "keywords": ["srtm", "elevation", "slope", "dem", "terrain"]},
}

# If automatic file matching picks the wrong file, name the files yourself:
#   FILE_OVERRIDES = {"power": ["my_weather_file.csv"], "srtm": ["elev.csv", "slope.csv"]}
FILE_OVERRIDES = {}

# ----------------------------------------------------------------------------
# Missing-value codes. These exact numbers are turned into NaN (blank).
# NASA POWER uses -999. -9999 is common in other exports.
# ----------------------------------------------------------------------------
SENTINEL_VALUES = [-999, -9999]

# ----------------------------------------------------------------------------
# Column-name detection (all names are compared AFTER cleaning: lowercase,
# letters/digits/underscores only, e.g. "system:time_start" -> "system_time_start")
# ----------------------------------------------------------------------------
YEAR_NAMES = ["year", "yyyy", "yr"]
MONTH_NAMES = ["mo", "month", "mon", "mm"]
DAY_NAMES = ["dy", "day", "dd"]
DOY_NAMES = ["doy", "day_of_year", "dayofyear", "jday"]
DATE_NAMES = ["date", "datetime", "timestamp", "time", "system_time_start",
              "year_month", "yyyymm", "yyyy_mm", "ym", "image_date",
              "acquisition_date", "yyyymmdd", "month"]

# Columns that identify a place/feature rather than a measurement.
# They are NOT treated as data values in monthly/daily tables.
ID_COLUMNS = ["lat", "latitude", "lon", "lng", "long", "longitude", "x", "y",
              "geo", "system_index", "id", "fid", "objectid", "point_id",
              "site", "name", "region", "district", "tehsil", "index"]

# ----------------------------------------------------------------------------
# Daily -> monthly aggregation (NASA POWER)
# ASSUMPTION: columns whose name contains one of these words are rainfall-type
# and are SUMMED over the month; every other column is AVERAGED.
# ----------------------------------------------------------------------------
SUM_COLUMN_HINTS = ["prec", "rain"]
# A month is set to NaN (not filled!) if fewer than this fraction of its days
# have a valid value.
MIN_VALID_DAY_FRACTION = 0.8

# Sanity ranges for NASA POWER columns, used ONLY to flag suspicious values.
# Values are never changed. A column not listed here gets no range check.
EXPECTED_DAILY_RANGES = {
    "t2m": (-50, 60), "t2m_max": (-50, 60), "t2m_min": (-50, 60),
    "t2mdew": (-60, 50), "t2mwet": (-60, 50),
    "prectotcorr": (0, 500), "prectot": (0, 500),
    "rh2m": (0, 100),
    "ws2m": (0, 50), "ws10m": (0, 60),
    "allsky_sfc_sw_dwn": (0, 40),
}

# MODIS LST: if values clearly look like Kelvin, ADD an extra column in degrees
# Celsius (original column is always kept). Set False to disable.
DERIVE_LST_CELSIUS = True

# ----------------------------------------------------------------------------
# Official SoilGrids (ISRIC) mapped-unit -> conventional-unit conversion
# factors. Conventional value = mapped (raw) value / factor. Source: ISRIC
# SoilGrids FAQ, "What do the target soil properties mean" table:
# https://www.isric.org/explore/soilgrids/faq-soilgrids#What_do_the_target_soil_properties_mean
# Applied ONLY to add a NEW derived column (same pattern as DERIVE_LST_CELSIUS
# above) - the original raw column is always kept unchanged.
# ----------------------------------------------------------------------------
SOILGRIDS_CONVERSIONS = {
    # column-name keyword: (divide raw value by this, conventional unit label)
    "clay": (10, "pct"),
    "sand": (10, "pct"),
    "silt": (10, "pct"),
    "nitrogen": (100, "g_per_kg"),
    "phh2o": (10, "ph"),
    "soc": (10, "g_per_kg"),
}

# QC flag only (values are never changed): if SRTM slope_max is more than this
# many times slope_mean, the max is likely a handful of outlier pixels (canal
# embankments, built structures, SRTM void-fill/edge noise), not
# representative terrain.
SLOPE_MAX_TO_MEAN_RATIO_FLAG = 5

# Static tables (soil / terrain): how to join them to the monthly master.
#  "none" -> join only tables that have exactly ONE row; keep others separate
#  "mean" -> if a table has several rows, average each numeric column
#            (crude: e.g. averages soil depth layers together - use with care)
STATIC_MULTI_ROW_MODE = "none"

# Shown in the data-quality report so nobody forgets them.
ASSUMPTIONS = [
    "File-to-dataset matching is done by keywords in the file name (see DATASETS in config.py).",
    "Column names are never hard-coded as required: dates and value columns are auto-detected and the result is printed and logged.",
    "NASA POWER -999 (and -9999 in any file) is treated as 'missing' and replaced with NaN.",
    "Monthly rainfall in NASA POWER columns whose name contains 'prec'/'rain' is SUMMED, all other daily columns are AVERAGED.",
    "A month with too few valid days (see MIN_VALID_DAY_FRACTION) is left as NaN, never filled or interpolated.",
    "If a monthly file has several rows per month (e.g. several points), they are AVERAGED per month and a warning is logged.",
    "Units are never silently converted. Only Kelvin->Celsius for MODIS LST is added (as a NEW column) when values clearly look like Kelvin.",
    "SoilGrids clay/sand/silt/nitrogen/phh2o/soc are stored as scaled integers. A derived column with the "
    "official ISRIC conversion factor (see SOILGRIDS_CONVERSIONS in config.py) is added; the raw column is kept.",
    "'image_count' columns (IMERG/NDVI/LST) are observation counts (half-hourly granules or satellite "
    "scenes), not measurements - they get their own unit note instead of the dataset's measurement note.",
    "SRTM: if slope_max is far above slope_mean (see SLOPE_MAX_TO_MEAN_RATIO_FLAG), this is flagged as a "
    "likely localized outlier/artifact, not a value change.",
    "Missing months stay as empty cells (NaN) in the master table. Nothing is interpolated or invented.",
]
