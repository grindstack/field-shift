"""
helpers.py - shared functions used by the three pipeline scripts.
Nothing here needs to be edited for normal use.
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

import config

# Make printing safe on Windows consoles
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")


# ----------------------------------------------------------------------------
# Small utilities
# ----------------------------------------------------------------------------
def ensure_dirs():
    for p in (config.RAW_DIR, config.PROCESSED_DIR, config.REPORT_DIR, config.FIGURE_DIR):
        p.mkdir(parents=True, exist_ok=True)


def clean_name(text):
    """'system:time_start' -> 'system_time_start', 'T2M ' -> 't2m'."""
    text = re.sub(r"[^0-9a-z]+", "_", str(text).strip().lower()).strip("_")
    return text or "unnamed"


def is_text(series):
    """True for text columns in both older (object) and newer (str) pandas."""
    return series.dtype == object or pd.api.types.is_string_dtype(series)


def first_present(columns, candidates):
    for cand in candidates:
        if cand in columns:
            return cand
    return None


def sanitize(obj):
    """Make anything JSON-safe (numpy numbers, NaN, Timestamps, Paths)."""
    if isinstance(obj, dict):
        return {str(k): sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [sanitize(v) for v in obj]
    if isinstance(obj, np.bool_):
        return bool(obj)
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, (float, np.floating)):
        return None if (np.isnan(obj) or np.isinf(obj)) else float(obj)
    if obj is None or isinstance(obj, (str, int, bool)):
        return obj
    return str(obj)


def save_json(obj, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sanitize(obj), f, indent=2)


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def new_record(key, source_name, kind, path):
    return {"dataset": key, "source_name": source_name, "kind": kind,
            "file": Path(path).name, "status": "ok", "notes": [], "warnings": [],
            "unit_checks": [], "outputs": {}}


def note(rec, msg):
    rec["notes"].append(msg)
    print("   - " + msg)


def warn(rec, msg):
    rec["warnings"].append(msg)
    print("   [WARNING] " + msg)


def missing_summary(df, cols=None):
    cols = list(df.columns) if cols is None else cols
    return {c: {"n_missing": int(df[c].isna().sum()),
                "pct_missing": round(100 * float(df[c].isna().mean()), 2)} for c in cols}


# ----------------------------------------------------------------------------
# Finding and reading files
# ----------------------------------------------------------------------------
def assign_files():
    """Return ({dataset: [paths]}, [unmatched paths])."""
    raw = config.RAW_DIR
    all_csv = sorted(p for p in raw.glob("*") if p.is_file() and p.suffix.lower() == ".csv")
    assigned = {k: [] for k in config.DATASETS}
    used = set()

    for key, names in config.FILE_OVERRIDES.items():
        for n in names:
            p = raw / n
            if p.exists():
                assigned[key].append(p)
                used.add(p)
            else:
                print(f"[WARNING] FILE_OVERRIDES: {p} does not exist")

    for p in all_csv:
        if p in used:
            continue
        lname = p.name.lower()
        for key, spec in config.DATASETS.items():
            if config.FILE_OVERRIDES.get(key):
                continue
            if any(k in lname for k in spec["keywords"]):
                assigned[key].append(p)
                used.add(p)
                break
    unmatched = [p for p in all_csv if p not in used]
    return assigned, unmatched


def read_csv_smart(path):
    """
    Read a CSV. Handles:
      - UTF-8 / Latin-1 text encodings
      - NASA POWER files that start with a text header ending in '-END HEADER-'
    Returns (DataFrame, header_lines). header_lines is the text above the table
    (NASA POWER puts the parameter UNITS there - read it!).
    """
    last_error = None
    for enc in ("utf-8-sig", "latin-1"):
        try:
            with open(path, "r", encoding=enc) as f:
                head = [next(f, "") for _ in range(300)]
            skip = 0
            header_lines = []
            for i, line in enumerate(head):
                if "-END HEADER-" in line.upper():
                    skip = i + 1
                    header_lines = [h.rstrip("\n") for h in head[:skip]]
                    break
            df = pd.read_csv(path, skiprows=skip, encoding=enc, low_memory=False)
            return df, header_lines
        except UnicodeDecodeError as e:
            last_error = e
    raise last_error


# ----------------------------------------------------------------------------
# Cleaning steps
# ----------------------------------------------------------------------------
def standardize_columns(df):
    mapping, seen, new_cols = {}, {}, []
    for c in df.columns:
        n = clean_name(c)
        if n in seen:
            seen[n] += 1
            n = f"{n}_{seen[n]}"
        else:
            seen[n] = 0
        new_cols.append(n)
        mapping[str(c)] = n
    df = df.copy()
    df.columns = new_cols
    return df, mapping


def basic_clean(df, rec):
    """Record raw info, standardize names, trim text, drop exact duplicate rows."""
    rec["rows_raw"] = int(len(df))
    rec["columns_raw"] = [str(c) for c in df.columns]
    rec["dtypes_raw"] = {str(c): str(t) for c, t in df.dtypes.items()}
    df, mapping = standardize_columns(df)
    rec["column_mapping"] = mapping
    for c in df.columns:
        if is_text(df[c]):
            df[c] = df[c].astype("object").where(df[c].isna(), df[c].astype(str).str.strip())
    n_dup = int(df.duplicated().sum())
    rec["exact_duplicates_removed"] = n_dup
    if n_dup:
        warn(rec, f"{n_dup} exact duplicate rows removed")
    df = df.drop_duplicates().reset_index(drop=True)
    return df


def coerce_numeric(df, rec, skip=()):
    """Turn text columns that are mostly numbers into numeric columns."""
    converted, lost = [], {}
    for c in df.columns:
        if c in skip or not is_text(df[c]):
            continue
        non_null = int(df[c].notna().sum())
        if non_null == 0:
            continue
        conv = pd.to_numeric(df[c], errors="coerce")
        if conv.notna().sum() / non_null >= 0.8:
            n_lost = int(non_null - conv.notna().sum())
            df[c] = conv
            converted.append(c)
            if n_lost:
                lost[c] = n_lost
    rec["numeric_columns_converted"] = converted
    rec["text_values_set_to_nan"] = lost
    for c, n in lost.items():
        warn(rec, f"column '{c}': {n} non-numeric text values became NaN")
    return df


def replace_sentinels(df, rec):
    """Replace missing-value codes (-999, -9999) with NaN and count them."""
    counts = {}
    for c in df.select_dtypes(include="number").columns:
        mask = df[c].isin(config.SENTINEL_VALUES)
        if mask.any():
            counts[c] = int(mask.sum())
            df[c] = df[c].astype(float).where(~mask)
    rec["sentinel_counts"] = counts
    if counts:
        note(rec, f"missing-value codes {config.SENTINEL_VALUES} replaced by NaN: {counts}")
    else:
        note(rec, f"no missing-value codes {config.SENTINEL_VALUES} found")
    return df


def drop_location_columns(df, rec):
    loc = [c for c in df.columns if c in config.ID_COLUMNS]
    if loc:
        n_places = len(df[loc].drop_duplicates())
        rec["location_columns_dropped"] = loc
        note(rec, f"identifier/location columns not used as data: {loc} ({n_places} distinct combinations)")
        if n_places > 1:
            warn(rec, "more than one location/feature found: rows are AVERAGED per date. "
                      "Check that this is what you want.")
        df = df.drop(columns=loc)
    return df


# ----------------------------------------------------------------------------
# Dates
# ----------------------------------------------------------------------------
def parse_date_series(s):
    """Parse a column into datetimes. Returns None if it does not look like dates."""
    if pd.api.types.is_numeric_dtype(s):
        v = s.dropna()
        if v.empty:
            return None
        mn, mx = float(v.min()), float(v.max())
        if mx >= 1e11:                                   # epoch milliseconds (Google Earth Engine)
            out = pd.to_datetime(s, unit="ms", errors="coerce")
        elif mx >= 1e9:                                  # epoch seconds
            out = pd.to_datetime(s, unit="s", errors="coerce")
        elif 19000101 <= mn and mx <= 21001231:          # 20160131
            out = pd.to_datetime(s.astype("Int64").astype(str), format="%Y%m%d", errors="coerce")
        elif 190001 <= mn and mx <= 210012:              # 201601
            out = pd.to_datetime(s.astype("Int64").astype(str), format="%Y%m", errors="coerce")
        else:
            return None
    else:
        try:
            out = pd.to_datetime(s, errors="coerce", utc=True, format="mixed")
        except (TypeError, ValueError):
            out = pd.to_datetime(s, errors="coerce", utc=True)
        out = out.dt.tz_localize(None)
    return out


def build_dates(df, kind):
    """
    Work out dates from the columns that exist. Tries, in order:
      1. year + month (+ day)  columns          e.g. NASA POWER YEAR, MO, DY
      2. year + day-of-year    (daily only)
      3. a single date/time column
    Returns (dates, columns_used, description). Raises ValueError if nothing fits.
    """
    cols = list(df.columns)
    year = first_present(cols, config.YEAR_NAMES)
    month = first_present(cols, config.MONTH_NAMES)
    day = first_present(cols, config.DAY_NAMES)
    doy = first_present(cols, config.DOY_NAMES)

    def numeric_between(c, lo, hi):
        return (c is not None and pd.api.types.is_numeric_dtype(df[c])
                and df[c].dropna().between(lo, hi).all())

    ok_year = numeric_between(year, 1900, 2100)
    ok_month = numeric_between(month, 1, 12)

    if kind == "daily" and ok_year and ok_month and numeric_between(day, 1, 31):
        dates = pd.to_datetime(pd.DataFrame({"year": df[year], "month": df[month], "day": df[day]}),
                               errors="coerce")
        return dates, [year, month, day], f"columns '{year}' + '{month}' + '{day}'"

    if kind == "daily" and ok_year and numeric_between(doy, 1, 366):
        base = pd.to_datetime(df[year].astype("Int64").astype(str), format="%Y", errors="coerce")
        dates = base + pd.to_timedelta(df[doy] - 1, unit="D")
        return dates, [year, doy], f"columns '{year}' + '{doy}' (day of year)"

    if kind == "monthly" and ok_year and ok_month:
        dates = pd.to_datetime(pd.DataFrame({"year": df[year], "month": df[month], "day": 1}),
                               errors="coerce")
        return dates, [year, month], f"columns '{year}' + '{month}' (day set to 1)"

    candidates = [c for c in config.DATE_NAMES if c in cols]
    candidates += [c for c in cols if ("date" in c or "time" in c) and c not in candidates]
    for c in candidates:
        parsed = parse_date_series(df[c])
        if parsed is not None and parsed.notna().mean() >= 0.5:
            if kind == "monthly":
                parsed = parsed.dt.to_period("M").dt.to_timestamp()
            else:
                parsed = parsed.dt.normalize()
            return parsed, [c], f"single date column '{c}'"

    raise ValueError("Could not find a date. Columns available: " + ", ".join(cols) +
                     ". Edit YEAR_NAMES / MONTH_NAMES / DATE_NAMES in config.py.")


# ----------------------------------------------------------------------------
# Unit / range checks (they only REPORT, they never change values)
# ----------------------------------------------------------------------------
def check_units(key, col, series, rec):
    v = series.dropna()
    if v.empty:
        warn(rec, f"column '{col}' is entirely empty")
        return None
    mn, md, mx = float(v.min()), float(v.median()), float(v.max())
    derived = None
    if col.endswith("image_count"):
        # ASSUMPTION: an "image_count" column counts source observations
        # (granules/scenes) behind the month's value - it is never the
        # measurement itself, so it must not reuse the dataset's unit rule.
        if key.startswith("imerg"):
            msg = ("count of half-hourly IMERG granules combined into this month (GPM IMERG native "
                   "temporal resolution is 30 min, so a full month = days_in_month * 48, e.g. 1488 for "
                   "31 days). This is an OBSERVATION COUNT, not a rainfall amount.")
        elif key.startswith("ndvi"):
            msg = ("count of Landsat scenes (cloud-free overpasses) used to compute this month's mean "
                   "NDVI. This is an OBSERVATION COUNT, not an NDVI value - no scale factor applies.")
        elif key.startswith("lst"):
            msg = ("count of MODIS scenes used to compute this month's mean LST. "
                   "This is an OBSERVATION COUNT, not a temperature value.")
        else:
            msg = "count of source images/observations behind this month's value, not a measurement."
        rec["unit_checks"].append({"column": col, "min": mn, "median": md, "max": mx, "note": msg})
        note(rec, f"unit check '{col}': {msg}")
        return None
    if key.startswith("ndvi"):
        if mn >= -1 and mx <= 1:
            msg = "values inside [-1, 1]: consistent with unscaled NDVI"
        elif mx > 1.5 and mx <= 10000:
            msg = "values exceed 1: may be scaled (e.g. x10000). NOT converted - confirm the scale factor"
        else:
            msg = "values outside the usual NDVI range - check source / masking"
    elif key.startswith("lst"):
        if 230 <= md <= 340:
            msg = "median looks like Kelvin"
            if config.DERIVE_LST_CELSIUS:
                derived = (series - 273.15, f"{col}_degc_derived")
                msg += f"; extra column '{col}_degc_derived' = value - 273.15 added (original kept)"
        elif -30 <= md <= 70:
            msg = "median looks like degrees Celsius"
        elif md >= 5000:
            msg = ("looks like RAW scaled MODIS integers (often x0.02 Kelvin). "
                   "NOT converted - confirm scale factor before use")
        else:
            msg = "unit unclear - NOT converted"
    elif key.startswith("imerg"):
        if mn < 0:
            msg = "NEGATIVE rainfall values found - check source"
        elif md < 2 and mx < 5:
            msg = "small values: GUESS = rate such as mm/hr (not a monthly total). Unit unverified, NOT converted"
        else:
            msg = "GUESS = accumulated mm per month. Unit unverified, NOT converted"
    else:
        msg = "no unit rule for this dataset - unit unverified"
    rec["unit_checks"].append({"column": col, "min": mn, "median": md, "max": mx, "note": msg})
    note(rec, f"unit check '{col}': {msg}")
    return derived


def static_unit_check(col, series, rec):
    """
    Heuristic unit/range notes for soil and terrain columns by column-name keywords.
    For known SoilGrids properties (clay/sand/silt/nitrogen/phh2o/soc), returns
    (derived_series, derived_col_name) using the official ISRIC conversion factor
    (config.SOILGRIDS_CONVERSIONS) so the caller can add it as a NEW column.
    The original column passed in is never modified.
    """
    v = series.dropna()
    if v.empty:
        return None
    mn, md, mx = float(v.min()), float(v.median()), float(v.max())
    msg = "no unit rule for this column - unit unverified"
    conv_key = None
    if any(k in col for k in ("elev", "srtm", "dem", "height")):
        msg = ("range looks plausible for metres (assumed). NOT converted" if -500 <= mn and mx <= 9000
               else "outside -500..9000: check units. NOT converted")
    elif "slope" in col:
        msg = ("within 0-90: consistent with degrees. NOT converted" if 0 <= mn and mx <= 90
               else "exceeds 90: may be percent grade, not degrees. NOT converted")
    elif re.search(r"(^|_)(phh2o|ph)(_|$)", col):
        conv_key = "phh2o"
    elif "nitrogen" in col:
        conv_key = "nitrogen"
    elif "soc" in col:
        conv_key = "soc"
    elif any(k in col for k in ("clay", "sand", "silt")):
        conv_key = next(k for k in ("clay", "sand", "silt") if k in col)

    derived = None
    if conv_key is not None and conv_key in config.SOILGRIDS_CONVERSIONS:
        factor, unit = config.SOILGRIDS_CONVERSIONS[conv_key]
        new_col = f"{col}_{unit}_derived"
        msg = (f"SoilGrids mapped/scaled unit (ISRIC convention: raw = conventional x {factor}). "
               f"Official conversion factor applied in NEW derived column '{new_col}' = raw / {factor} "
               f"(conventional unit: {unit}); original column kept unchanged.")
        derived = (series / factor, new_col)

    rec["unit_checks"].append({"column": col, "min": mn, "median": md, "max": mx, "note": msg})
    note(rec, f"unit check '{col}': {msg}")
    return derived


def check_slope_outliers(df, value_cols, rec):
    """
    Cross-column QC (flags only, never changes values): if a '*_max' slope
    column is far above the matching '*_mean' slope column, the max is likely
    driven by a handful of outlier pixels (canal embankments, built
    structures, roads, or SRTM void-fill/edge noise) rather than
    representative terrain - common over an otherwise flat alluvial plain.
    """
    max_col = next((c for c in value_cols if "slope" in c and c.endswith("max")), None)
    mean_col = next((c for c in value_cols if "slope" in c and c.endswith("mean")), None)
    if max_col is None or mean_col is None:
        return
    mx, mn = df[max_col].dropna(), df[mean_col].dropna()
    if mx.empty or mn.empty or float(mn.iloc[0]) <= 0:
        return
    mx_val, mn_val = float(mx.iloc[0]), float(mn.iloc[0])
    ratio = mx_val / mn_val
    if ratio >= config.SLOPE_MAX_TO_MEAN_RATIO_FLAG:
        warn(rec, f"'{max_col}' ({mx_val:.2f} deg) is {ratio:.1f}x '{mean_col}' ({mn_val:.2f} deg). "
                  "Likely a small number of outlier pixels (canal embankments, built structures, roads, "
                  "or SRTM void-fill/edge noise), not representative field slope. Suggested check: pull "
                  "the slope histogram or p90/p95 percentile (not just min/mean/max) from the source, or "
                  "inspect the slope raster for the pixel(s) driving the max, before using max slope in "
                  "any model.")


# ----------------------------------------------------------------------------
# Dataset processors
# ----------------------------------------------------------------------------
def prefixed(source_name, col):
    return col if col.startswith(source_name) else f"{source_name}_{col}"


def process_daily(key, source_name, df, rec):
    df = basic_clean(df, rec)
    dates, used, how = build_dates(df, "daily")
    rec["date_method"] = how
    note(rec, f"dates built from {how}")
    df = df.drop(columns=[c for c in used if c in df.columns])
    df["date"] = dates
    bad = int(df["date"].isna().sum())
    rec["rows_unparseable_dates_dropped"] = bad
    if bad:
        warn(rec, f"{bad} rows with unreadable dates dropped")
        df = df.dropna(subset=["date"])
    df = drop_location_columns(df, rec)
    df = coerce_numeric(df, rec, skip=["date"])
    df = replace_sentinels(df, rec)

    value_cols = [c for c in df.columns if c != "date" and pd.api.types.is_numeric_dtype(df[c])]
    text_cols = [c for c in df.columns if c != "date" and c not in value_cols]
    rec["dropped_text_columns"] = text_cols
    if text_cols:
        note(rec, f"non-numeric columns dropped from the time series: {text_cols}")
    df = df[["date"] + value_cols]

    dup = int(df["date"].duplicated().sum())
    rec["duplicate_dates_merged"] = dup
    if dup:
        warn(rec, f"{dup} rows share a date with another row: averaged per date")
        df = df.groupby("date", as_index=False)[value_cols].mean()
    df = df.sort_values("date").reset_index(drop=True)

    # Range checks
    flagged = []
    for c in value_cols:
        rng = config.EXPECTED_DAILY_RANGES.get(c)
        if rng is None:
            rec["unit_checks"].append({"column": c, "min": df[c].min(), "median": df[c].median(),
                                       "max": df[c].max(),
                                       "note": "no sanity range defined; unit unverified (see source header)"})
            continue
        n_out = int(((df[c] < rng[0]) | (df[c] > rng[1])).sum())
        rec["unit_checks"].append({"column": c, "min": df[c].min(), "median": df[c].median(),
                                   "max": df[c].max(),
                                   "note": f"{n_out} values outside {rng}" if n_out else f"all values inside {rng}"})
        if n_out:
            flagged.append(c)
            warn(rec, f"column '{c}': {n_out} values outside expected range {rng} (kept unchanged)")

    # Completeness against the study window
    start = pd.Timestamp(config.START_MONTH + "-01")
    end = pd.Timestamp(config.END_MONTH + "-01") + pd.offsets.MonthEnd(0)
    expected = pd.date_range(start, end, freq="D")
    present = pd.DatetimeIndex(df["date"]).intersection(expected)
    rec.update({"date_min": df["date"].min(), "date_max": df["date"].max(),
                "expected_periods": len(expected), "present_periods": len(present),
                "missing_periods_count": len(expected) - len(present)})
    if len(expected) - len(present):
        warn(rec, f"{len(expected) - len(present)} of {len(expected)} expected days are absent from the file")
    outside = int((~pd.DatetimeIndex(df["date"]).isin(expected)).sum())
    if outside:
        warn(rec, f"{outside} rows fall outside {config.START_MONTH}..{config.END_MONTH} (kept here, dropped in master)")

    rec["rows_after"] = int(len(df))
    rec["value_columns"] = value_cols
    rec["missing_after"] = missing_summary(df, value_cols)
    return df, value_cols


def daily_to_monthly(source_name, daily, value_cols, rec):
    """Aggregate daily data to months. Months with too few valid days -> NaN."""
    d = daily.set_index("date")
    period = d.index.to_period("M")
    valid = d[value_cols].notna().groupby(period).sum()
    days_in_month = pd.Series(valid.index.days_in_month, index=valid.index)
    frac = valid.div(days_in_month, axis=0)

    out = pd.DataFrame(index=valid.index)
    rules, masked = {}, {}
    for c in value_cols:
        is_sum = any(h in c for h in config.SUM_COLUMN_HINTS)
        g = d[c].groupby(period)
        col = g.sum(min_count=1) if is_sum else g.mean()
        too_few = frac[c] < config.MIN_VALID_DAY_FRACTION
        masked[c] = int(too_few.sum())
        col = col.where(~too_few)
        name = prefixed(source_name, c)
        out[name] = col
        out[name + "_n_valid_days"] = valid[c].astype(int)
        rules[name] = "sum" if is_sum else "mean"
    out.index = out.index.to_timestamp()
    out.index.name = "month"
    out = out.reset_index()
    rec["monthly_aggregation_rules"] = rules
    rec["monthly_months_set_to_nan_too_few_days"] = masked
    note(rec, f"daily -> monthly rules (ASSUMPTION): {rules}")
    for c, n in masked.items():
        if n:
            warn(rec, f"'{c}': {n} months set to NaN (fewer than {config.MIN_VALID_DAY_FRACTION:.0%} valid days)")
    return out


def process_monthly(key, source_name, df, rec):
    df = basic_clean(df, rec)
    dates, used, how = build_dates(df, "monthly")
    rec["date_method"] = how
    note(rec, f"months built from {how}")
    df = df.drop(columns=[c for c in used if c in df.columns])
    df["month"] = dates
    bad = int(df["month"].isna().sum())
    rec["rows_unparseable_dates_dropped"] = bad
    if bad:
        warn(rec, f"{bad} rows with unreadable dates dropped")
        df = df.dropna(subset=["month"])
    df = drop_location_columns(df, rec)
    df = coerce_numeric(df, rec, skip=["month"])
    df = replace_sentinels(df, rec)

    value_cols = [c for c in df.columns if c != "month" and pd.api.types.is_numeric_dtype(df[c])]
    text_cols = [c for c in df.columns if c != "month" and c not in value_cols]
    rec["dropped_text_columns"] = text_cols
    if text_cols:
        note(rec, f"non-numeric columns dropped: {text_cols}")
    if not value_cols:
        raise ValueError("No numeric value column found. Columns: " + ", ".join(df.columns))
    df = df[["month"] + value_cols]

    dup = int(df["month"].duplicated().sum())
    rec["duplicate_dates_merged"] = dup
    if dup:
        warn(rec, f"{dup} extra rows for the same month: AVERAGED per month")
        df = df.groupby("month", as_index=False)[value_cols].mean()
    df = df.sort_values("month").reset_index(drop=True)

    rename = {c: prefixed(source_name, c) for c in value_cols}
    df = df.rename(columns=rename)
    value_cols = list(rename.values())
    rec["renamed_value_columns"] = rename

    for c in list(value_cols):
        derived = check_units(key, c, df[c], rec)
        if derived is not None:
            df[derived[1]] = derived[0]
            value_cols.append(derived[1])

    expected = pd.date_range(config.START_MONTH + "-01", config.END_MONTH + "-01", freq="MS")
    present = pd.DatetimeIndex(df["month"]).intersection(expected)
    missing_months = expected.difference(present)
    rec.update({"date_min": df["month"].min(), "date_max": df["month"].max(),
                "expected_periods": len(expected), "present_periods": len(present),
                "missing_periods_count": len(missing_months),
                "missing_periods_sample": [d.strftime("%Y-%m") for d in missing_months[:24]]})
    if len(missing_months):
        warn(rec, f"{len(missing_months)} of {len(expected)} expected months are absent")
    rec["rows_after"] = int(len(df))
    rec["value_columns"] = value_cols
    rec["missing_after"] = missing_summary(df, value_cols)
    return df, value_cols


def process_static(key, source_name, df, rec):
    df = basic_clean(df, rec)
    df = coerce_numeric(df, rec)
    df = replace_sentinels(df, rec)
    value_cols = [c for c in df.select_dtypes(include="number").columns if c not in config.ID_COLUMNS]
    for c in list(value_cols):
        derived = static_unit_check(c, df[c], rec)
        if derived is not None:
            df[derived[1]] = derived[0]
            value_cols.append(derived[1])
    check_slope_outliers(df, value_cols, rec)
    rec["value_columns"] = value_cols
    rec["rows_after"] = int(len(df))
    rec["missing_after"] = missing_summary(df, list(df.columns))
    if len(df) > 1:
        note(rec, f"table has {len(df)} rows (e.g. several points or soil depth layers) - see STATIC_MULTI_ROW_MODE")
    return df


def static_feature_row(source_name, df, value_cols):
    """
    Decide whether a static table can be joined to the monthly master.
    Returns (dict_of_features or None, explanation).
    """
    if not value_cols:
        return None, "no numeric columns"
    if len(df) == 1:
        row = df[value_cols].iloc[0]
        why = "single row: joined as constant columns"
    elif config.STATIC_MULTI_ROW_MODE == "mean":
        row = df[value_cols].mean()
        why = f"{len(df)} rows AVERAGED (STATIC_MULTI_ROW_MODE='mean') - check this is meaningful"
    else:
        return None, (f"{len(df)} rows: kept separate, NOT joined. "
                      "Set STATIC_MULTI_ROW_MODE='mean' in config.py to average them, or reshape manually")
    return {prefixed(source_name, c): row[c] for c in value_cols}, why
