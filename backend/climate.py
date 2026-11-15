"""
Historical climate/static context for the Field Shift decision engine.

Loads the already-processed datasets from data/processed/ (never the raw
files, never re-run preprocessing). Supplies CONTEXT ONLY - nothing here
drives a pass/fail Result (research/decision_engine_spec.md sec 6).

image_count columns (imerg_image_count, ndvi_image_count, lst_image_count)
are deliberately excluded from every agricultural measurement - they are
observation-coverage metadata, not measurements (spec sec 2 and 6).
"""
import json
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
MASTER_MONTHLY_PATH = PROCESSED_DIR / "master_monthly.csv"
MASTER_STATIC_PATH = PROCESSED_DIR / "master_monthly_with_static.csv"
CROP_PROFILES_PATH = PROCESSED_DIR / "crop_profiles.json"

HISTORICAL_PERIOD_LABEL = "2016-2025"

# column -> (human label, always-shown-by-default)
AG_MEASUREMENT_COLUMNS = {
    "imerg_rainfall_mm": ("IMERG monthly rainfall (mm)", True),
    "power_prectotcorr": ("NASA POWER monthly precipitation (mm) - comparison figure", True),
    "power_t2m": ("NASA POWER mean air temperature (deg C)", True),
    "lst_mean_lst_c": ("MODIS mean land-surface temperature (deg C) - NOT air temperature", True),
    "ndvi_mean_ndvi": ("Landsat mean NDVI - optional vegetation-greenness context only", False),
}
EXCLUDED_COVERAGE_COLUMNS = ["imerg_image_count", "ndvi_image_count", "lst_image_count"]

_master_cache = None
_profiles_cache = None


def load_master():
    global _master_cache
    if _master_cache is None:
        _master_cache = pd.read_csv(MASTER_MONTHLY_PATH, parse_dates=["month"])
    return _master_cache


def load_crop_profiles():
    global _profiles_cache
    if _profiles_cache is None:
        with open(CROP_PROFILES_PATH, "r", encoding="utf-8") as f:
            _profiles_cache = json.load(f)
    return _profiles_cache


def scenario_sources(scenario_key):
    """scenario_key: 'baseline' or 'alternative'."""
    profiles = load_crop_profiles()
    scenario = profiles.get("scenarios", {}).get(scenario_key, {})
    return scenario.get("sources", [])


def concise_climate_summary(month_filter=None, include_ndvi=True):
    """
    month_filter: optional list of calendar months (1-12) to restrict to.
    Returns a concise historical (2016-2025) summary - mean/min/max per
    measurement column - never the full monthly series.
    """
    df = load_master()
    if month_filter:
        df = df[df["month_of_year"].isin(month_filter)]

    statistics = {}
    for col, (label, default_shown) in AG_MEASUREMENT_COLUMNS.items():
        if col == "ndvi_mean_ndvi" and not include_ndvi:
            continue
        if col not in df.columns:
            continue
        series = df[col].dropna()
        if series.empty:
            continue
        statistics[col] = {
            "label": label,
            "default_shown": default_shown,
            "mean": round(float(series.mean()), 2),
            "min": round(float(series.min()), 2),
            "max": round(float(series.max()), 2),
        }

    return {
        "period": HISTORICAL_PERIOD_LABEL,
        "months_included": sorted(int(m) for m in df["month_of_year"].unique()) if month_filter else "all (1-12)",
        "note": "Historical observations only; not a forecast for an upcoming season.",
        "excluded_columns": EXCLUDED_COVERAGE_COLUMNS,
        "excluded_columns_reason": "observation-coverage metadata (granule/scene counts), not measurements",
        "statistics": statistics,
    }


def detailed_monthly_series():
    """Full monthly time series, 2016-2025 - optional expansion only (spec sec 6)."""
    df = load_master()
    cols = ["month", "month_of_year", "year"] + [c for c in AG_MEASUREMENT_COLUMNS if c in df.columns]
    out = df[cols].copy()
    out["month"] = out["month"].dt.strftime("%Y-%m-%d")
    for c in out.columns:
        if out[c].dtype.kind == "f":
            out[c] = out[c].round(3)
    return out.to_dict(orient="records")


def district_static_context():
    """
    Single-sample-point SoilGrids/SRTM context. Explicitly district-level,
    never presented as a farm-level measurement (spec sec 2, 6).
    """
    df = pd.read_csv(MASTER_STATIC_PATH, nrows=1)
    row = df.iloc[0]

    def g(col):
        return float(row[col]) if col in df.columns and pd.notna(row[col]) else None

    return {
        "scope": "district-level single sample point (SoilGrids/SRTM) - NOT a farm-level measurement",
        "soil_0_5cm": {
            "clay_pct": g("soil_clay_0_5cm_mean_pct_derived"),
            "sand_pct": g("soil_sand_0_5cm_mean_pct_derived"),
            "ph": g("soil_phh2o_0_5cm_mean_ph_derived"),
            "nitrogen_g_per_kg": g("soil_nitrogen_0_5cm_mean_g_per_kg_derived"),
            "soc_g_per_kg": g("soil_soc_0_5cm_mean_g_per_kg_derived"),
        },
        "terrain": {
            "elevation_m_mean": g("srtm_elevation_m_mean"),
            "slope_degrees_mean": g("srtm_slope_degrees_mean"),
            "slope_degrees_max": g("srtm_slope_degrees_max"),
            "caveat": (
                "slope_degrees_max is far above slope_degrees_mean in the source "
                "data - likely a small number of outlier pixels (embankments, "
                "structures, SRTM void-fill noise), not representative field slope."
            ),
        },
        "farmer_soil_test_overrides_this": True,
    }
